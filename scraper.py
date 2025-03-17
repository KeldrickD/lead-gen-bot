import time
import pandas as pd
import random
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from utils import load_config, wait_with_random_delay, is_valid_business_profile, detect_business_type, extract_owner_name, logger, simulate_human_typing

class LeadScraper:
    def __init__(self):
        self.config = load_config()
        self.leads = []
        self.driver = None
        self.wait = None
    
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
    
    def login_to_instagram(self):
        """Log in to Instagram with credentials from environment variables."""
        try:
            # Get credentials from environment variables
            username = os.environ.get("INSTAGRAM_USERNAME")
            password = os.environ.get("INSTAGRAM_PASSWORD")
            
            if not username or not password:
                logger.error("Instagram credentials not found in environment variables")
                return False
            
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
            logger.error(f"Error during Instagram login: {e}")
            return False
    
    def search_instagram_hashtag(self, hashtag):
        """Search Instagram for posts with a specific hashtag."""
        try:
            self.driver.get(f"https://www.instagram.com/explore/tags/{hashtag}/")
            wait_with_random_delay(3, 5)
            
            # Scroll down to load more posts
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                wait_with_random_delay(2, 3)
            
            # Find post links
            post_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
            post_urls = [link.get_attribute("href") for link in post_links[:20]]  # Limit to 20 posts
            
            logger.info(f"Found {len(post_urls)} posts for hashtag #{hashtag}")
            return post_urls
        except Exception as e:
            logger.error(f"Error searching hashtag #{hashtag}: {e}")
            return []
    
    def extract_profile_from_post(self, post_url):
        """Visit a post and extract the profile information of the poster."""
        try:
            self.driver.get(post_url)
            wait_with_random_delay(2, 4)
            
            # Click on the username to go to the profile
            username_element = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href, '/') and not(contains(@href, '/p/'))]")))
            profile_url = username_element.get_attribute("href")
            username = username_element.text
            
            # Visit the profile
            self.driver.get(profile_url)
            wait_with_random_delay(2, 4)
            
            # Extract profile data
            profile_data = {}
            
            try:
                profile_data["username"] = username
                profile_data["profile_url"] = profile_url
                
                # Extract full name
                try:
                    full_name_element = self.driver.find_element(By.XPATH, "//h1")
                    profile_data["full_name"] = full_name_element.text
                except:
                    profile_data["full_name"] = username
                
                # Extract bio
                try:
                    bio_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'biography')]")
                    profile_data["bio"] = bio_element.text
                except:
                    profile_data["bio"] = ""
                
                # Extract website
                try:
                    website_element = self.driver.find_element(By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'instagram.com'))]")
                    profile_data["website"] = website_element.get_attribute("href")
                except:
                    profile_data["website"] = ""
                
                # Extract follower count
                try:
                    followers_element = self.driver.find_element(By.XPATH, "//a[contains(@href, '/followers/')]/span")
                    followers_text = followers_element.text
                    profile_data["followers_count"] = self._parse_count(followers_text)
                except:
                    profile_data["followers_count"] = 0
                
                # Determine if it's a business profile
                if is_valid_business_profile(profile_data):
                    profile_data["business_type"] = detect_business_type(profile_data)
                    profile_data["owner_name"] = extract_owner_name(profile_data)
                    return profile_data
                else:
                    return None
                
            except Exception as e:
                logger.error(f"Error extracting profile data: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting profile from post {post_url}: {e}")
            return None
    
    def _parse_count(self, count_text):
        """Parse follower count from text (e.g., '1.2K', '5M')."""
        count_text = count_text.replace(",", "")
        if "K" in count_text:
            return int(float(count_text.replace("K", "")) * 1000)
        elif "M" in count_text:
            return int(float(count_text.replace("M", "")) * 1000000)
        else:
            try:
                return int(count_text)
            except:
                return 0
    
    def collect_leads_from_instagram(self, hashtags=None, max_leads=100):
        """Scrape business profiles from Instagram based on hashtags."""
        if not hashtags:
            hashtags = self.config.get("lead_sources", {}).get("instagram_hashtags", [])
        
        if not self.setup_driver():
            return []
        
        if not self.login_to_instagram():
            self.driver.quit()
            return []
        
        leads = []
        for hashtag in hashtags:
            logger.info(f"Scraping leads from hashtag #{hashtag}")
            
            post_urls = self.search_instagram_hashtag(hashtag)
            for post_url in post_urls:
                if len(leads) >= max_leads:
                    break
                
                profile_data = self.extract_profile_from_post(post_url)
                if profile_data:
                    leads.append(profile_data)
                    logger.info(f"Found lead: {profile_data['username']} ({profile_data['business_type']})")
                
                # Add a random delay between post visits
                wait_with_random_delay(2, 5)
            
            if len(leads) >= max_leads:
                break
        
        self.driver.quit()
        return leads
    
    def export_leads_to_csv(self, leads, filename="leads.csv"):
        """Export collected leads to a CSV file."""
        try:
            df = pd.DataFrame(leads)
            df.to_csv(filename, index=False)
            logger.info(f"Exported {len(leads)} leads to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting leads to CSV: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    scraper = LeadScraper()
    leads = scraper.collect_leads_from_instagram(max_leads=20)
    if leads:
        scraper.export_leads_to_csv(leads)
    logger.info("Lead scraping complete") 