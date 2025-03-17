import time
import random
import logging
import os
from datetime import datetime, timedelta
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from utils import (
    load_config, 
    wait_with_random_delay, 
    logger, 
    simulate_human_typing, 
    enforce_platform_limits,
    format_timestamp
)
from message_generator import MessageGenerator
from chatbot import chatbot, ChatbotResponse

class DMSender:
    def __init__(self):
        self.config = load_config()
        self.driver = None
        self.wait = None
        self.message_generator = MessageGenerator()
        self.session_stats = self.load_session_stats()
        self.use_ai_chatbot = self.config.get("use_ai_chatbot", True)
    
    def load_session_stats(self):
        """Load or initialize session statistics for tracking DM sending."""
        try:
            if os.path.exists('session_stats.json'):
                with open('session_stats.json', 'r') as f:
                    stats = json.load(f)
                
                # Check if we need to reset daily counters
                today = datetime.now().strftime('%Y-%m-%d')
                if stats.get('date') != today:
                    # Reset daily counters if it's a new day
                    stats = {
                        'date': today,
                        'platforms': {
                            'instagram': {'daily_count': 0, 'total_count': stats.get('platforms', {}).get('instagram', {}).get('total_count', 0)},
                            'facebook': {'daily_count': 0, 'total_count': stats.get('platforms', {}).get('facebook', {}).get('total_count', 0)},
                            'linkedin': {'daily_count': 0, 'total_count': stats.get('platforms', {}).get('linkedin', {}).get('total_count', 0)},
                            'twitter': {'daily_count': 0, 'total_count': stats.get('platforms', {}).get('twitter', {}).get('total_count', 0)}
                        },
                        'last_dm_time': stats.get('last_dm_time', None)
                    }
                
                return stats
            else:
                # Initialize with default values
                today = datetime.now().strftime('%Y-%m-%d')
                return {
                    'date': today,
                    'platforms': {
                        'instagram': {'daily_count': 0, 'total_count': 0},
                        'facebook': {'daily_count': 0, 'total_count': 0},
                        'linkedin': {'daily_count': 0, 'total_count': 0},
                        'twitter': {'daily_count': 0, 'total_count': 0}
                    },
                    'last_dm_time': None
                }
        except Exception as e:
            logger.error(f"Error loading session stats: {e}")
            # Return default values on error
            today = datetime.now().strftime('%Y-%m-%d')
            return {
                'date': today,
                'platforms': {
                    'instagram': {'daily_count': 0, 'total_count': 0},
                    'facebook': {'daily_count': 0, 'total_count': 0},
                    'linkedin': {'daily_count': 0, 'total_count': 0},
                    'twitter': {'daily_count': 0, 'total_count': 0}
                },
                'last_dm_time': None
            }
    
    def save_session_stats(self):
        """Save current session statistics to file."""
        try:
            with open('session_stats.json', 'w') as f:
                json.dump(self.session_stats, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving session stats: {e}")
            return False
    
    def update_session_stats(self, platform):
        """Update session statistics after sending a DM."""
        platform_stats = self.session_stats['platforms'].get(platform, {'daily_count': 0, 'total_count': 0})
        
        # Update counters
        platform_stats['daily_count'] = platform_stats.get('daily_count', 0) + 1
        platform_stats['total_count'] = platform_stats.get('total_count', 0) + 1
        
        # Update last DM time
        self.session_stats['last_dm_time'] = format_timestamp()
        
        # Save the updated stats
        self.session_stats['platforms'][platform] = platform_stats
        self.save_session_stats()
    
    def setup_driver(self):
        """Set up and configure the Selenium WebDriver."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            
            # Add random user agent to avoid detection
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            ]
            options.add_argument(f"user-agent={random.choice(user_agents)}")
            
            # Add these options to help with common issues
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # Comment out the following line for debugging
            # options.add_argument("--headless")
            
            try:
                # Try using a specific version of ChromeDriver
                service = Service(ChromeDriverManager(version="114.0.5735.90").install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.warning(f"Error using ChromeDriverManager: {e}")
                
                # Fallback: Try using the system's Chrome installation
                logger.info("Falling back to default Chrome installation")
                self.driver = webdriver.Chrome(options=options)
            
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("WebDriver setup complete")
            return True
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            return False
    
    def login_to_platform(self, platform):
        """Log in to a social media platform (Instagram, Facebook, LinkedIn, Twitter)."""
        # Get credentials from environment variables instead of config
        username = os.environ.get(f"{platform.upper()}_USERNAME")
        password = os.environ.get(f"{platform.upper()}_PASSWORD")
        
        if not username or not password:
            logger.error(f"{platform.capitalize()} credentials not found in environment variables")
            return False
        
        try:
            if platform == "instagram":
                return self._login_to_instagram(username, password)
            elif platform == "facebook":
                return self._login_to_facebook(username, password)
            elif platform == "linkedin":
                return self._login_to_linkedin(username, password)
            elif platform == "twitter":
                return self._login_to_twitter(username, password)
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False
        except Exception as e:
            logger.error(f"Error logging in to {platform}: {e}")
            return False
    
    def _login_to_instagram(self, username, password):
        """Log in to Instagram."""
        try:
            self.driver.get("https://www.instagram.com/")
            wait_with_random_delay(3, 5)
            
            # Accept cookies if prompted
            try:
                cookie_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
                cookie_button.click()
                wait_with_random_delay(1, 2)
            except:
                logger.info("No cookie prompt found or already accepted")
            
            # Enter username
            username_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
            username_field.clear()
            # Use human-like typing for credentials
            simulate_human_typing(self.driver, username_field, username)
            wait_with_random_delay(1, 2)
            
            # Enter password
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            password_field.clear()
            simulate_human_typing(self.driver, password_field, password)
            wait_with_random_delay(1, 2)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for the login to complete
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/direct/inbox/')]")))
                logger.info("Successfully logged in to Instagram")
                return True
            except TimeoutException:
                logger.error("Login unsuccessful or unexpected page after login")
                return False
        except Exception as e:
            logger.error(f"Error logging in to Instagram: {e}")
            return False
    
    def _login_to_facebook(self, username, password):
        """Log in to Facebook."""
        try:
            self.driver.get("https://www.facebook.com/")
            wait_with_random_delay(3, 5)
            
            # Accept cookies if prompted
            try:
                cookie_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")))
                cookie_button.click()
                wait_with_random_delay(1, 2)
            except:
                logger.info("No cookie prompt found or already accepted")
            
            # Enter email/username
            email_field = self.wait.until(EC.element_to_be_clickable((By.ID, "email")))
            email_field.clear()
            simulate_human_typing(self.driver, email_field, username)
            wait_with_random_delay(1, 2)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            simulate_human_typing(self.driver, password_field, password)
            wait_with_random_delay(1, 2)
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for the login to complete
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Messenger' or contains(@class, 'messenger')]")))
                logger.info("Successfully logged in to Facebook")
                return True
            except TimeoutException:
                logger.error("Login unsuccessful or unexpected page after login")
                return False
        except Exception as e:
            logger.error(f"Error logging in to Facebook: {e}")
            return False
    
    def _login_to_linkedin(self, username, password):
        """Log in to LinkedIn."""
        # Implementation similar to Instagram/Facebook
        logger.info("LinkedIn login not fully implemented yet")
        return False
    
    def _login_to_twitter(self, username, password):
        """Log in to Twitter."""
        # Implementation similar to Instagram/Facebook
        logger.info("Twitter login not fully implemented yet")
        return False
    
    def send_instagram_dm(self, target_username, message_data):
        """Send a direct message to a target Instagram user."""
        try:
            # Navigate to the user's profile
            self.driver.get(f"https://www.instagram.com/{target_username}/")
            wait_with_random_delay(3, 5)
            
            # Check if user exists
            if "Sorry, this page isn't available." in self.driver.page_source:
                logger.warning(f"Instagram user {target_username} not found")
                return False
            
            # Click on Message button
            try:
                message_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Message')]"))
                )
                message_btn.click()
                wait_with_random_delay(2, 4)
            except Exception as e:
                logger.warning(f"Could not click 'Message' button for {target_username}: {e}")
                return False
            
            # Handle any popups that might appear
            try:
                not_now_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_btn.click()
                wait_with_random_delay(1, 2)
            except:
                # No popup appeared, continue
                pass
            
            # Find the message input and send message
            try:
                message_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                )
                
                # Type the message with human-like typing
                simulate_human_typing(message_input, message_data["text"])
                
                # Send the message
                message_input.send_keys(Keys.ENTER)
                wait_with_random_delay(1, 2)
                
                # Log success
                logger.info(f"Successfully sent DM to {target_username} on Instagram")
                
                # Update session stats
                self.update_session_stats("instagram")
                
                # Enable AI chatbot monitoring for this conversation if configured
                if self.use_ai_chatbot:
                    self._start_ai_conversation_monitoring(target_username, "instagram", message_data)
                
                return True
                
            except Exception as e:
                logger.error(f"Error sending message to {target_username} on Instagram: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error accessing Instagram profile for {target_username}: {e}")
            return False

    def _start_ai_conversation_monitoring(self, username, platform, message_data):
        """Start monitoring a conversation with the AI chatbot."""
        try:
            # Register initial message in the chatbot system
            lead_id = message_data.get("lead_id", username)
            
            # Create initial system message to establish context
            initial_context = {
                "lead_id": lead_id,
                "platform": platform,
                "message": f"Initial outreach sent: {message_data['text']}",
                "metadata": {
                    "is_new_lead": True,
                    "username": username,
                    "business_name": message_data.get("business_name", ""),
                    "business_type": message_data.get("business_type", ""),
                    "owner_name": message_data.get("owner_name", ""),
                    "initial_message_sent": True,
                    "initial_message_time": format_timestamp(datetime.now())
                }
            }
            
            # Register with chatbot
            chatbot.add_message(lead_id, platform, "assistant", message_data["text"])
            
            logger.info(f"Started AI chatbot monitoring for {username} on {platform}")
            
        except Exception as e:
            logger.error(f"Error setting up AI chatbot for {username} on {platform}: {e}")

    def check_for_responses(self, platform, max_conversations=10):
        """Check for responses to messages and engage with AI chatbot."""
        if not self.use_ai_chatbot:
            logger.info("AI chatbot is disabled. Skipping response checks.")
            return
            
        try:
            # Log start of checking
            logger.info(f"Checking for new messages on {platform}...")
            
            if platform == "instagram":
                self._check_instagram_responses(max_conversations)
            elif platform == "facebook":
                self._check_facebook_responses(max_conversations)
            elif platform == "linkedin":
                self._check_linkedin_responses(max_conversations)
            elif platform == "twitter":
                self._check_twitter_responses(max_conversations)
            else:
                logger.warning(f"Response checking not implemented for {platform}")
                
        except Exception as e:
            logger.error(f"Error checking for responses on {platform}: {e}")

    def _check_instagram_responses(self, max_conversations=10):
        """Check for new Instagram direct messages and respond using the AI chatbot."""
        try:
            # Navigate to Instagram direct messages
            self.driver.get("https://www.instagram.com/direct/inbox/")
            wait_with_random_delay(3, 5)
            
            # Check for any popups and dismiss them
            try:
                not_now_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_btn.click()
                wait_with_random_delay(1, 2)
            except:
                # No popup appeared, continue
                pass
                
            # Find conversations with unread messages (look for blue dot indicator)
            try:
                unread_conversations = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'unread')]"))
                )
                
                # Limit to max_conversations
                unread_conversations = unread_conversations[:max_conversations]
                
                if not unread_conversations:
                    logger.info("No new Instagram messages found")
                    return
                    
                logger.info(f"Found {len(unread_conversations)} unread Instagram conversations")
                
                # Process each unread conversation
                for conversation in unread_conversations:
                    try:
                        # Click on the conversation
                        conversation.click()
                        wait_with_random_delay(2, 3)
                        
                        # Get username from conversation
                        username_element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'username')]"))
                        )
                        username = username_element.text.strip()
                        
                        # Get the most recent message from the user
                        messages = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'message-content')]"))
                        )
                        
                        # Get the last message that's not from us
                        last_user_message = None
                        for message in reversed(messages):
                            # Check if this is from the other user (not our own message)
                            if "message-sender-self" not in message.get_attribute("class"):
                                last_user_message = message.text.strip()
                                break
                                
                        if not last_user_message:
                            logger.warning(f"No user message found in conversation with {username}")
                            continue
                            
                        logger.info(f"Processing message from {username}: {last_user_message[:50]}...")
                        
                        # Process with AI chatbot
                        response = chatbot.process_message(
                            lead_id=username,
                            platform="instagram",
                            message_content=last_user_message
                        )
                        
                        # Send the response
                        message_input = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
                        )
                        
                        # Type the AI response with human-like typing
                        simulate_human_typing(message_input, response.message)
                        
                        # Send the message
                        message_input.send_keys(Keys.ENTER)
                        wait_with_random_delay(2, 4)
                        
                        logger.info(f"Sent AI response to {username} on Instagram")
                        
                    except Exception as e:
                        logger.error(f"Error processing Instagram conversation: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error finding unread Instagram conversations: {e}")
                
        except Exception as e:
            logger.error(f"Error checking Instagram responses: {e}")
    
    def send_facebook_dm(self, target_username, message_data):
        """Send a DM to a target user on Facebook."""
        # Implementation similar to Instagram
        logger.info("Facebook DM sending not fully implemented yet")
        return False
    
    def send_batch_dms(self, platform, leads, message_type="initial", use_gpt=True, max_dms=None):
        """Send a batch of direct messages to leads on the specified platform."""
        if not leads:
            logger.warning(f"No leads provided for {platform}")
            return []
            
        # Set up the driver if not already done
        if not self.driver:
            self.setup_driver()
            
        # Login to the platform if needed
        if not self.login_to_platform(platform):
            logger.error(f"Failed to login to {platform}")
            return []
            
        # Check platform limits
        max_allowed = enforce_platform_limits(platform, self.session_stats)
        if max_allowed <= 0:
            logger.warning(f"Daily limit reached for {platform}. No messages will be sent.")
            return []
            
        # Adjust max_dms based on platform limits
        if not max_dms or max_dms > max_allowed:
            max_dms = max_allowed
            
        logger.info(f"Sending up to {max_dms} DMs on {platform}")
        
        # Track successful sends
        successful_sends = []
        
        # Process each lead up to the maximum
        for i, lead in enumerate(leads[:max_dms]):
            if platform == "instagram":
                username = lead.get("username")
                if not username:
                    logger.warning(f"No username provided for lead {i}")
                    continue
                    
                # Generate message
                message_data = self.message_generator.generate_message(lead, message_type, use_gpt)
                message_data["lead_id"] = lead.get("id", username)
                
                # Send message
                if self.send_instagram_dm(username, message_data):
                    successful_sends.append({
                        "platform": platform,
                        "username": username,
                        "message_type": message_type,
                        "timestamp": format_timestamp(datetime.now())
                    })
                    
                # Add random delay between messages
                wait_with_random_delay(10, 30)
                
            elif platform == "facebook":
                # Similar implementation for Facebook
                pass
                
            elif platform == "linkedin":
                # Similar implementation for LinkedIn
                pass
                
            elif platform == "twitter":
                # Similar implementation for Twitter
                pass
            
        logger.info(f"Successfully sent {len(successful_sends)} DMs on {platform}")
        return successful_sends
        
    def check_and_respond_to_messages(self, platform, max_conversations=5):
        """Check for new messages and respond using the AI chatbot."""
        # Set up the driver if not already done
        if not self.driver:
            self.setup_driver()
            
        # Login to the platform if needed
        if not self.login_to_platform(platform):
            logger.error(f"Failed to login to {platform}")
            return
            
        # Check for responses
        self.check_for_responses(platform, max_conversations)

if __name__ == "__main__":
    # Example usage
    sender = DMSender()
    
    # Test lead data
    test_leads = [
        {
            "username": "test_account1",
            "full_name": "Test Business 1",
            "owner_name": "John",
            "business_type": "Barbershop"
        },
        {
            "username": "test_account2",
            "full_name": "Test Business 2",
            "owner_name": "Sarah",
            "business_type": "Fitness Studio"
        }
    ]
    
    # Send test messages
    sent_messages = sender.send_batch_dms("instagram", test_leads, max_dms=2)
    
    for msg in sent_messages:
        print(f"Sent to {msg['username']}: {msg['message']}") 