import json
import os
import logging
import time
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lead-gen-bot")

def load_config():
    """Load configuration from config.json file."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def get_random_delay(min_seconds=1, max_seconds=5):
    """Generate a random delay to mimic human behavior."""
    return random.uniform(min_seconds, max_seconds)

def wait_with_random_delay(min_seconds=1, max_seconds=5):
    """Wait for a random amount of time to avoid detection."""
    delay = get_random_delay(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def format_timestamp():
    """Return a formatted timestamp for the current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_valid_business_profile(profile_data):
    """Check if a profile meets the criteria to be considered a business profile."""
    # Example criteria: has a bio, has a website, has more than 100 followers
    if not profile_data:
        return False
    
    has_bio = profile_data.get("bio") and len(profile_data.get("bio")) > 5
    has_website = profile_data.get("website")
    has_followers = profile_data.get("followers_count", 0) > 100
    
    return has_bio and (has_website or has_followers)

def detect_business_type(profile_data):
    """Analyze a profile to determine the type of business."""
    bio = profile_data.get("bio", "").lower()
    business_types = load_config().get("lead_sources", {}).get("business_types", [])
    
    # Check for business keywords in the bio
    for business_type in business_types:
        if business_type.lower() in bio:
            return business_type
    
    # Default to "Business" if no specific type is detected
    return "Business"

def extract_owner_name(profile_data):
    """Try to extract the owner's name from profile data."""
    fullname = profile_data.get("full_name", "")
    if fullname:
        # Try to get the first name
        first_name = fullname.split()[0]
        return first_name
    
    # Fallback to username if full name isn't available
    username = profile_data.get("username", "")
    if username:
        # Clean up username to get a potential name
        cleaned_name = ''.join([c for c in username if c.isalpha()])
        if cleaned_name:
            return cleaned_name[:1].upper() + cleaned_name[1:].lower()
    
    return ""  # Return empty string if no name could be extracted

# New functions for enhancements

def send_email_notification(subject, message_body, importance="normal"):
    """Send email notification about important bot events."""
    # Get email configuration from environment
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    sender_email = os.environ.get("NOTIFICATION_EMAIL")
    sender_password = os.environ.get("NOTIFICATION_EMAIL_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    
    if not all([sender_email, sender_password, recipient_email]):
        logger.warning("Email notification settings not complete, skipping notification")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = f"LeadGen Bot: {subject}"
        
        # Add priority header for important notifications
        if importance == "high":
            msg["X-Priority"] = "1"
            msg["X-MSMail-Priority"] = "High"
        
        # Add message body
        msg.attach(MIMEText(message_body, "plain"))
        
        # Connect to server and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logger.info(f"Email notification sent: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False

def notify_warm_lead(lead_data):
    """Send notification for a new warm lead."""
    username = lead_data.get("username")
    platform = lead_data.get("platform")
    business_name = lead_data.get("lead_data", {}).get("full_name", "Unknown business")
    
    subject = f"New Warm Lead: {business_name}"
    message = f"""
A new warm lead has responded positively:

Platform: {platform}
Username: {username}
Business: {business_name}
Time: {format_timestamp()}

Login to your account to respond promptly.
"""
    send_email_notification(subject, message, importance="high")

def simulate_human_typing(driver, element, text, min_delay=0.05, max_delay=0.25):
    """Simulate human typing with random delays between keystrokes."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def enforce_platform_limits(platform, daily_dm_count):
    """Check if we've exceeded the daily limits for a platform."""
    config = load_config()
    platform_config = config.get("social_platforms", {}).get(platform, {})
    daily_limit = platform_config.get("daily_dm_limit", 15)
    
    # Check if we're approaching or exceeding the limit
    if daily_dm_count >= daily_limit:
        logger.warning(f"Daily DM limit reached for {platform}: {daily_dm_count}/{daily_limit}")
        return False
    elif daily_dm_count >= daily_limit * 0.8:
        logger.warning(f"Approaching daily DM limit for {platform}: {daily_dm_count}/{daily_limit}")
    
    return True

def daily_stats_report():
    """Generate a daily stats report for the bot's activity."""
    # This would typically read from the lead tracker data
    try:
        with open("leads_data.json", "r") as f:
            leads_data = json.load(f)
        
        # Count today's activities
        today = datetime.now().strftime("%Y-%m-%d")
        
        sent_today = sum(1 for msg in leads_data.get("sent_messages", []) 
                         if msg.get("timestamp", "").startswith(today))
        
        responses_today = sum(1 for resp in leads_data.get("responses", []) 
                             if resp.get("response_timestamp", "").startswith(today))
        
        follow_ups_today = sum(1 for follow in leads_data.get("follow_ups", []) 
                              if follow.get("timestamp", "").startswith(today))
        
        warm_leads_today = sum(1 for lead in leads_data.get("warm_leads", []) 
                              if lead.get("recorded_at", "").startswith(today))
        
        # Create report
        subject = f"LeadGen Bot Daily Report - {today}"
        message = f"""
DAILY ACTIVITY REPORT - {today}

Messages Sent: {sent_today}
Responses Received: {responses_today}
Follow-ups Sent: {follow_ups_today}
New Warm Leads: {warm_leads_today}

Response Rate: {responses_today/sent_today*100:.1f}% (if sent_today > 0 else 'N/A')
Conversion Rate: {warm_leads_today/responses_today*100:.1f}% (if responses_today > 0 else 'N/A')

Total stats to date:
Total Messages Sent: {len(leads_data.get("sent_messages", []))}
Total Responses: {len(leads_data.get("responses", []))}
Total Warm Leads: {len(leads_data.get("warm_leads", []))}
"""
        
        send_email_notification(subject, message)
        logger.info("Daily stats report generated and sent")
        return True
    except Exception as e:
        logger.error(f"Error generating daily stats report: {e}")
        return False 