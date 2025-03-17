import os
import json
import time
import schedule
import argparse
import logging
import random
from datetime import datetime, timedelta
import sys
import csv
import string
import threading
from dotenv import load_dotenv
import traceback
import subprocess

from utils import load_config, format_timestamp, logger, setup_logger, send_notification
from scraper import LeadScraper
from message_generator import MessageGenerator
from dm_sender import DMSender
from lead_tracker import LeadTracker
from analytics import Analytics
from optimizer import MessageOptimizer
from api import start_api
from chatbot import chatbot

# Set up logging
logger = setup_logger('lead-gen-bot')

# Load environment variables
load_dotenv()

# Constants
MAX_LEADS_DEFAULT = 50
MAX_DMS_DEFAULT = 25

class LeadGenBot:
    def __init__(self):
        self.config = load_config()
        self.scraper = LeadScraper()
        self.message_generator = MessageGenerator()
        self.sender = DMSender()
        self.tracker = LeadTracker()
    
    def collect_new_leads(self, platform="instagram", max_leads=20, test_mode=False):
        """Collect new leads from the specified platform."""
        logger.info(f"Starting lead collection from {platform}")
        
        if test_mode:
            # Generate simulated leads for testing
            logger.info("Using test mode to generate simulated leads")
            leads = self.generate_test_leads(max_leads)
            
            if leads:
                self.scraper.export_leads_to_csv(leads, f"{platform}_leads_{datetime.now().strftime('%Y%m%d')}_test.csv")
                logger.info(f"Generated {len(leads)} simulated leads for testing")
            return leads
        elif platform == "instagram":
            leads = self.scraper.collect_leads_from_instagram(max_leads=max_leads)
            if leads:
                self.scraper.export_leads_to_csv(leads, f"{platform}_leads_{datetime.now().strftime('%Y%m%d')}.csv")
                logger.info(f"Collected {len(leads)} leads from {platform}")
            else:
                logger.warning(f"No leads collected from {platform}")
            return leads
        else:
            logger.warning(f"Lead collection from {platform} not implemented yet")
            return []
    
    def generate_test_leads(self, count=5):
        """Generate simulated leads for testing purposes."""
        business_types = self.config.get("lead_sources", {}).get("business_types", [])
        
        test_leads = []
        for i in range(count):
            business_type = random.choice(business_types)
            username = f"test_user_{i+1}"
            full_name = f"Test {business_type} {i+1}"
            
            lead = {
                "username": username,
                "profile_url": f"https://www.instagram.com/{username}/",
                "full_name": full_name,
                "bio": f"This is a test {business_type.lower()} business for lead generation testing.",
                "website": f"https://www.test{business_type.lower().replace(' ', '')}.com",
                "followers_count": random.randint(500, 5000),
                "business_type": business_type,
                "owner_name": f"Owner{i+1}"
            }
            
            test_leads.append(lead)
        
        return test_leads
    
    def send_initial_messages(self, platform="instagram", leads=None, max_dms=None, test_mode=False):
        """Send initial messages to leads on the specified platform."""
        if not leads:
            logger.warning("No leads provided for sending initial messages")
            return []
        
        logger.info(f"Sending initial messages to {len(leads)} leads on {platform}")
        
        if test_mode:
            # Simulate sending messages for testing
            logger.info("Using test mode to simulate message sending")
            sent_messages = self.simulate_message_sending(platform, leads, "initial", max_dms)
        else:
            sent_messages = self.sender.send_batch_dms(platform, leads, message_type="initial", use_gpt=True, max_dms=max_dms)
        
        # Record sent messages
        for message in sent_messages:
            self.tracker.record_sent_message(message)
        
        logger.info(f"Sent {len(sent_messages)} initial messages on {platform}")
        return sent_messages
    
    def simulate_message_sending(self, platform, leads, message_type="initial", max_dms=None):
        """Simulate sending messages for testing purposes."""
        if max_dms and max_dms < len(leads):
            leads = leads[:max_dms]
        
        sent_messages = []
        for lead in leads:
            # Generate a message
            message_data = self.message_generator.generate_message(lead, message_type=message_type, use_gpt=False)
            
            # Create a record as if the message was sent
            message_record = {
                "platform": platform,
                "username": lead.get("username"),
                "lead_data": lead,
                "message": message_data.get("text", ""),
                "template_id": message_data.get("template_id", "unknown"),
                "message_type": message_type,
                "timestamp": format_timestamp()
            }
            
            sent_messages.append(message_record)
            logger.info(f"Simulated sending message to {lead.get('username')} on {platform}")
            
            # Add a small delay to simulate real sending
            time.sleep(random.uniform(0.5, 1.5))
        
        return sent_messages
    
    def send_follow_up_messages(self, platform="instagram", test_mode=False):
        """Send follow-up messages to leads that haven't responded."""
        logger.info(f"Checking for leads that need follow-up on {platform}")
        
        # Get leads that need follow-up
        leads_to_follow_up = self.tracker.get_leads_to_follow_up()
        
        if not leads_to_follow_up:
            logger.info("No leads need follow-up at this time")
            return []
        
        # Filter leads by platform
        platform_leads = [lead for lead in leads_to_follow_up if lead.get("platform") == platform]
        
        if not platform_leads:
            logger.info(f"No leads on {platform} need follow-up at this time")
            return []
        
        logger.info(f"Sending follow-up messages to {len(platform_leads)} leads on {platform}")
        
        follow_up_messages = []
        
        if test_mode:
            # Simulate sending follow-up messages
            follow_up_messages = self.simulate_message_sending(platform, platform_leads, "follow_up")
            
            # Record follow-ups
            for message in follow_up_messages:
                follow_up_data = {
                    "platform": platform,
                    "username": message.get("username"),
                    "original_message": message.get("lead_data", {}).get("original_message", ""),
                    "follow_up_message": message.get("message", ""),
                    "timestamp": format_timestamp(),
                    "status": "Sent",
                    "lead_data": message.get("lead_data", {})
                }
                self.tracker.record_follow_up(follow_up_data)
        else:
            for lead in platform_leads:
                # Generate follow-up message
                follow_up_message = self.message_generator.generate_message(
                    lead.get("lead_data", {}), 
                    message_type="follow_up", 
                    use_gpt=True
                )
                
                username = lead.get("username")
                success = False
                
                if platform == "instagram":
                    # Set up the sender
                    if not self.sender.setup_driver():
                        logger.error("Failed to set up WebDriver for follow-up messages")
                        break
                    
                    if not self.sender.login_to_platform(platform):
                        logger.error(f"Failed to log in to {platform} for follow-up messages")
                        self.sender.driver.quit()
                        break
                    
                    # Send the follow-up message
                    success = self.sender.send_instagram_dm(username, follow_up_message)
                
                if success:
                    # Record the follow-up
                    follow_up_data = {
                        "platform": platform,
                        "username": username,
                        "original_message": lead.get("original_message", ""),
                        "follow_up_message": follow_up_message.get("text", ""),
                        "timestamp": format_timestamp(),
                        "status": "Sent",
                        "lead_data": lead.get("lead_data", {})
                    }
                    
                    self.tracker.record_follow_up(follow_up_data)
                    follow_up_messages.append(follow_up_data)
                    logger.info(f"Sent follow-up message to {username} on {platform}")
                
                # Wait between messages
                time.sleep(5)
            
            # Close the browser if it's open
            if hasattr(self.sender, 'driver') and self.sender.driver:
                self.sender.driver.quit()
        
        logger.info(f"Sent {len(follow_up_messages)} follow-up messages on {platform}")
        return follow_up_messages
    
    def check_for_responses(self, platform="instagram", test_mode=False):
        """
        Check for responses to our messages.
        
        Note: This is a placeholder function. In a real implementation, you would need to:
        1. Use the platform's API to check for responses, or
        2. Use Selenium to log in and check the inbox, or
        3. Use a webhook/notification system provided by the platform
        
        For now, this is just a demonstration of how the function would work.
        """
        logger.info(f"Checking for responses on {platform}")
        
        if test_mode:
            # Simulate some responses for testing
            sent_messages = self.tracker.leads_data.get("sent_messages", [])
            if not sent_messages:
                logger.info("No messages found to simulate responses")
                return []
            
            # Choose random messages to simulate responses (about 20% of them)
            response_count = max(1, int(len(sent_messages) * 0.2))
            messages_to_respond = random.sample(sent_messages, min(response_count, len(sent_messages)))
            
            responses = []
            for message in messages_to_respond:
                response_text = random.choice([
                    "Hey, I'm interested! Can you tell me more about your services?",
                    "Thanks for reaching out. What are your rates?",
                    "I've been thinking about getting a website. What would you recommend for my business?",
                    "How soon can you deliver a website?",
                    "Do you have some examples of your work?"
                ])
                
                response_data = {
                    "platform": message.get("platform"),
                    "username": message.get("username"),
                    "lead_data": message.get("lead_data", {}),
                    "original_message": message.get("message", ""),
                    "response_message": response_text,
                    "response_timestamp": format_timestamp(),
                    "status": "New"
                }
                
                self.tracker.record_response(response_data)
                responses.append(response_data)
                logger.info(f"Simulated response from {message.get('username')} on {platform}")
            
            logger.info(f"Simulated {len(responses)} responses on {platform}")
            return responses
        else:
            # In a real implementation, this would check for actual responses
            # For demo purposes, we'll just log that the check was performed
            logger.info("Response checking functionality not fully implemented")
            
            # Return an empty list as we're not actually checking for responses
            return []
    
    def run_daily_workflow(self, test_mode=False):
        """Run the complete daily workflow for lead generation."""
        logger.info("Starting daily lead generation workflow")
        
        # Step 1: Collect new leads
        platform = "instagram"  # Can be expanded to other platforms
        new_leads = self.collect_new_leads(platform, max_leads=20, test_mode=test_mode)
        
        # Step 2: Send initial messages to new leads
        if new_leads:
            sent_messages = self.send_initial_messages(platform, new_leads, max_dms=15, test_mode=test_mode)
        
        # Step 3: Send follow-up messages to leads that haven't responded
        follow_up_messages = self.send_follow_up_messages(platform, test_mode=test_mode)
        
        # Step 4: Check for responses (placeholder)
        responses = self.check_for_responses(platform, test_mode=test_mode)
        
        # Step 5: Export the updated leads data
        self.tracker.export_leads_to_csv(f"leads_export_{datetime.now().strftime('%Y%m%d')}.csv")
        
        logger.info("Daily lead generation workflow completed")
        return {
            "new_leads": len(new_leads) if new_leads else 0,
            "sent_messages": len(sent_messages) if 'sent_messages' in locals() else 0,
            "follow_ups": len(follow_up_messages),
            "responses": len(responses)
        }

def setup_scheduler(test_mode=False):
    """Set up the scheduler for recurring tasks."""
    bot = LeadGenBot()
    
    # Schedule daily lead collection and initial messages
    if test_mode:
        schedule.every(1).minutes.do(bot.run_daily_workflow, test_mode=True)
    else:
        schedule.every().day.at("09:00").do(bot.run_daily_workflow)
        
        # Schedule follow-up checks multiple times per day
        schedule.every().day.at("12:00").do(bot.send_follow_up_messages, platform="instagram")
        schedule.every().day.at("17:00").do(bot.send_follow_up_messages, platform="instagram")
        
        # Schedule response checks throughout the day
        for hour in range(9, 21, 2):  # Check every 2 hours from 9 AM to 8 PM
            schedule.every().day.at(f"{hour:02d}:30").do(bot.check_for_responses, platform="instagram")
    
    logger.info("Scheduler set up successfully")
    return schedule

def setup_argparse():
    """Set up command-line argument parsing."""
    parser = argparse.ArgumentParser(description='LeadGen Bot')
    
    # Main action argument
    parser.add_argument('--action', type=str, required=True, 
                        choices=['scrape', 'message', 'check_messages', 'schedule', 'dashboard', 'api', 'run_all', 'chatbot', 'test'],
                        help='Action to perform')
    
    # Optional arguments for fine-tuning behavior
    parser.add_argument('--platform', type=str, default='instagram',
                        choices=['instagram', 'facebook', 'linkedin', 'twitter', 'all'],
                        help='Social media platform to use')
    parser.add_argument('--hashtags', type=str, nargs='+',
                        help='Hashtags to search for')
    parser.add_argument('--max_leads', type=int, default=20,
                        help='Maximum number of leads to collect')
    parser.add_argument('--max_dms', type=int, default=None,
                        help='Maximum number of DMs to send')
    parser.add_argument('--message_type', type=str, default='initial',
                        choices=['initial', 'follow_up'],
                        help='Type of message to send')
    parser.add_argument('--use_gpt', action='store_true', default=True,
                        help='Use GPT for message generation')
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode with simulated data')
    parser.add_argument('--max_conversations', type=int, default=10,
                        help='Maximum number of conversations to check for responses')
    
    return parser

def check_messages(args):
    """Check for new messages and respond using the AI chatbot."""
    logger.info("Checking for new messages and responding with AI chatbot")
    
    try:
        # Initialize the DM sender
        dm_sender = DMSender()
        
        # Configure platforms to check
        platforms = []
        if args.platform == 'all':
            platforms = ['instagram', 'facebook', 'linkedin', 'twitter']
        else:
            platforms = [args.platform]
            
        for platform in platforms:
            logger.info(f"Checking messages on {platform}")
            dm_sender.check_and_respond_to_messages(platform, args.max_conversations)
            
        logger.info("Message checking and response completed")
        
    except Exception as e:
        logger.error(f"Error checking messages: {e}")
        logger.error(traceback.format_exc())

def run_chatbot_api(args):
    """Run the chatbot API server."""
    logger.info("Starting chatbot API server...")
    
    try:
        # Start the API server
        start_api()
    except Exception as e:
        logger.error(f"Error starting chatbot API: {e}")
        logger.error(traceback.format_exc())

def run_chatbot_followups():
    """Run the chatbot follow-up process."""
    logger.info("Running chatbot follow-up process...")
    
    try:
        # Check for inactive conversations and send follow-ups
        chatbot.check_inactive_conversations()
        logger.info("Chatbot follow-up process completed")
    except Exception as e:
        logger.error(f"Error in chatbot follow-up process: {e}")
        logger.error(traceback.format_exc())

def run_scheduled_tasks():
    """Run all scheduled tasks."""
    config = load_config()
    schedule_config = config.get("schedule", {})
    
    # Get preferred platforms
    platforms = config.get("preferred_platforms", ["instagram"])
    
    # Schedule lead collection
    if schedule_config.get("scrape_enabled", True):
        scrape_time = schedule_config.get("scrape_time", "09:00")
        logger.info(f"Scheduling lead collection at {scrape_time}")
        schedule.every().day.at(scrape_time).do(
            collect_new_leads, 
            {'platform': 'instagram', 'max_leads': 50, 'test': False}
        )
    
    # Schedule messaging
    if schedule_config.get("message_enabled", True):
        message_time = schedule_config.get("message_time", "10:30")
        logger.info(f"Scheduling messaging at {message_time}")
        schedule.every().day.at(message_time).do(
            send_initial_messages, 
            {'platform': 'instagram', 'max_dms': 30, 'test': False}
        )
    
    # Schedule message checking and response
    if schedule_config.get("check_messages_enabled", True):
        check_intervals = schedule_config.get("check_messages_interval", 60)  # in minutes
        logger.info(f"Scheduling message checking every {check_intervals} minutes")
        schedule.every(check_intervals).minutes.do(
            check_messages,
            argparse.Namespace(platform='instagram', max_conversations=10)
        )
    
    # Schedule chatbot follow-ups
    if schedule_config.get("chatbot_followup_enabled", True):
        followup_time = schedule_config.get("followup_time", "18:00")
        logger.info(f"Scheduling chatbot follow-ups at {followup_time}")
        schedule.every().day.at(followup_time).do(run_chatbot_followups)
    
    # Start the scheduler
    logger.info("Scheduler set up successfully. Running continuously.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        logger.error(traceback.format_exc())
        # Send notification if scheduler fails
        send_notification(
            subject="LeadGen Bot Scheduler Error",
            message=f"Error in scheduler: {str(e)}\n\n{traceback.format_exc()}"
        )

def run_all(args):
    """Run all main bot functions in sequence."""
    # First collect leads
    collect_new_leads(args)
    
    # Then send messages
    send_initial_messages(args)
    
    # Finally check for responses
    check_messages(args)

def main():
    """Main function to parse arguments and run the appropriate action."""
    # Parse command line arguments
    parser = setup_argparse()
    args = parser.parse_args()
    
    logger.info(f"Starting LeadGen Bot with action: {args.action}")
    
    try:
        # Run the appropriate action based on the command line argument
        if args.action == 'scrape':
            collect_new_leads(args)
        elif args.action == 'message':
            send_initial_messages(args)
        elif args.action == 'check_messages':
            check_messages(args)
        elif args.action == 'schedule':
            run_scheduled_tasks()
        elif args.action == 'dashboard':
            # Start the dashboard server
            from dashboard import run_dashboard
            run_dashboard()
        elif args.action == 'api':
            # Start the API server
            run_chatbot_api(args)
        elif args.action == 'run_all':
            run_all(args)
        elif args.action == 'chatbot':
            # Start both API server and check for messages
            api_thread = threading.Thread(target=run_chatbot_api, args=(args,))
            api_thread.daemon = True
            api_thread.start()
            
            # Start message checking in a separate thread
            checker_thread = threading.Thread(target=check_messages, args=(args,))
            checker_thread.daemon = True
            checker_thread.start()
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Chatbot services stopped by user")
        else:
            logger.error(f"Unknown action: {args.action}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(traceback.format_exc())
        # Send notification if bot fails
        send_notification(
            subject="LeadGen Bot Error",
            message=f"Error running bot: {str(e)}\n\n{traceback.format_exc()}"
        )
        sys.exit(1)
    
    logger.info(f"LeadGen Bot completed action: {args.action}")

if __name__ == "__main__":
    main() 