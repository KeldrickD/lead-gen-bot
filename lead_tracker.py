import os
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import logging

from utils import load_config, format_timestamp, logger, notify_warm_lead, daily_stats_report

class LeadTracker:
    def __init__(self, local_storage_file="leads_data.json"):
        self.config = load_config()
        self.local_storage_file = local_storage_file
        self.leads_data = self.load_leads_data()
        self.setup_google_sheets()
    
    def load_leads_data(self):
        """Load the leads data from the local JSON file."""
        try:
            if os.path.exists(self.local_storage_file):
                with open(self.local_storage_file, "r") as f:
                    return json.load(f)
            return {"sent_messages": [], "responses": [], "follow_ups": [], "warm_leads": []}
        except Exception as e:
            logger.error(f"Error loading leads data: {e}")
            return {"sent_messages": [], "responses": [], "follow_ups": [], "warm_leads": []}
    
    def save_leads_data(self):
        """Save the leads data to the local JSON file."""
        try:
            with open(self.local_storage_file, "w") as f:
                json.dump(self.leads_data, f, indent=2)
            logger.info(f"Saved leads data to {self.local_storage_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving leads data: {e}")
            return False
    
    def setup_google_sheets(self):
        """Set up the Google Sheets API client."""
        try:
            # Get credentials file directly from environment variable instead of config
            credentials_file = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE", "google_credentials.json")
            
            if not credentials_file or not os.path.exists(credentials_file):
                logger.warning(f"Google Sheets credentials file not found: {credentials_file}")
                self.sheets_client = None
                return False
            
            # Set up the credentials
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            self.sheets_client = gspread.authorize(credentials)
            
            # Get the spreadsheet ID directly from environment variable
            spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
            if not spreadsheet_id:
                logger.warning("Google Sheets spreadsheet ID not found in environment variables")
                self.spreadsheet = None
                return False
            
            logger.info(f"Attempting to open spreadsheet with ID: {spreadsheet_id}")
            self.spreadsheet = self.sheets_client.open_by_key(spreadsheet_id)
            logger.info(f"Google Sheets setup complete - Connected to: {self.spreadsheet.title}")
            
            # Initialize spreadsheet worksheets if they don't exist
            self._init_spreadsheet_worksheets()
            
            return True
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            self.sheets_client = None
            self.spreadsheet = None
            return False
    
    def _init_spreadsheet_worksheets(self):
        """Initialize the necessary worksheets in the Google Spreadsheet."""
        if not self.spreadsheet:
            return
        
        # List of worksheets to initialize
        worksheet_names = ["Sent Messages", "Responses", "Follow Ups", "Warm Leads"]
        
        # Get existing worksheet names
        existing_worksheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for name in worksheet_names:
            if name not in existing_worksheets:
                self.spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
                worksheet = self.spreadsheet.worksheet(name)
                
                # Set up headers based on worksheet type
                if name == "Sent Messages":
                    headers = ["Platform", "Username", "Business Name", "Business Type", "Owner Name", "Message", "Timestamp", "Message Type"]
                elif name == "Responses":
                    headers = ["Platform", "Username", "Business Name", "Business Type", "Owner Name", "Original Message", "Response", "Response Timestamp", "Status"]
                elif name == "Follow Ups":
                    headers = ["Platform", "Username", "Business Name", "Business Type", "Owner Name", "Original Message", "Follow Up Message", "Follow Up Timestamp", "Status"]
                elif name == "Warm Leads":
                    headers = ["Platform", "Username", "Business Name", "Business Type", "Owner Name", "Conversation Link", "Status", "Notes"]
                
                worksheet.insert_row(headers, 1)
                logger.info(f"Created worksheet: {name}")
    
    def record_sent_message(self, message_data):
        """Record a sent message in both local storage and Google Sheets."""
        # Add the message to local storage
        self.leads_data["sent_messages"].append(message_data)
        self.save_leads_data()
        
        # Add the message to Google Sheets if available
        if self.spreadsheet:
            try:
                worksheet = self.spreadsheet.worksheet("Sent Messages")
                
                row = [
                    message_data.get("platform", ""),
                    message_data.get("username", ""),
                    message_data.get("lead_data", {}).get("full_name", ""),
                    message_data.get("lead_data", {}).get("business_type", ""),
                    message_data.get("lead_data", {}).get("owner_name", ""),
                    message_data.get("message", ""),
                    message_data.get("timestamp", format_timestamp()),
                    message_data.get("message_type", "initial")
                ]
                
                worksheet.append_row(row)
                logger.info(f"Recorded sent message to {message_data.get('username')} in Google Sheets")
            except Exception as e:
                logger.error(f"Error recording sent message in Google Sheets: {e}")
        
        return True
    
    def record_response(self, response_data):
        """Record a response from a lead in both local storage and Google Sheets."""
        # Add the response to local storage
        self.leads_data["responses"].append(response_data)
        self.save_leads_data()
        
        # Add the response to Google Sheets if available
        if self.spreadsheet:
            try:
                worksheet = self.spreadsheet.worksheet("Responses")
                
                row = [
                    response_data.get("platform", ""),
                    response_data.get("username", ""),
                    response_data.get("lead_data", {}).get("full_name", ""),
                    response_data.get("lead_data", {}).get("business_type", ""),
                    response_data.get("lead_data", {}).get("owner_name", ""),
                    response_data.get("original_message", ""),
                    response_data.get("response_message", ""),
                    response_data.get("response_timestamp", format_timestamp()),
                    response_data.get("status", "New")
                ]
                
                worksheet.append_row(row)
                logger.info(f"Recorded response from {response_data.get('username')} in Google Sheets")
            except Exception as e:
                logger.error(f"Error recording response in Google Sheets: {e}")
        
        # Check if this is a warm lead and record it
        if self.is_positive_response(response_data.get("response_message", "")):
            self.record_warm_lead(response_data)
        
        return True
    
    def record_follow_up(self, follow_up_data):
        """Record a follow-up message in both local storage and Google Sheets."""
        # Add the follow-up to local storage
        self.leads_data["follow_ups"].append(follow_up_data)
        self.save_leads_data()
        
        # Add the follow-up to Google Sheets if available
        if self.spreadsheet:
            try:
                worksheet = self.spreadsheet.worksheet("Follow Ups")
                
                row = [
                    follow_up_data.get("platform", ""),
                    follow_up_data.get("username", ""),
                    follow_up_data.get("lead_data", {}).get("full_name", ""),
                    follow_up_data.get("lead_data", {}).get("business_type", ""),
                    follow_up_data.get("lead_data", {}).get("owner_name", ""),
                    follow_up_data.get("original_message", ""),
                    follow_up_data.get("follow_up_message", ""),
                    follow_up_data.get("timestamp", format_timestamp()),
                    follow_up_data.get("status", "Sent")
                ]
                
                worksheet.append_row(row)
                logger.info(f"Recorded follow-up to {follow_up_data.get('username')} in Google Sheets")
            except Exception as e:
                logger.error(f"Error recording follow-up in Google Sheets: {e}")
        
        return True
    
    def record_warm_lead(self, lead_data):
        """Record a warm lead in both local storage and Google Sheets."""
        # Generate a simple conversation link (in a real implementation, this would be a link to the conversation)
        platform = lead_data.get("platform", "")
        username = lead_data.get("username", "")
        conversation_link = f"https://www.{platform}.com/direct/t/{username}"
        
        warm_lead = {
            "platform": platform,
            "username": username,
            "lead_data": lead_data.get("lead_data", {}),
            "conversation_link": conversation_link,
            "status": "New",
            "notes": "Responded positively",
            "recorded_at": format_timestamp()
        }
        
        # Add to local storage
        self.leads_data["warm_leads"].append(warm_lead)
        self.save_leads_data()
        
        # Add to Google Sheets if available
        if self.spreadsheet:
            try:
                worksheet = self.spreadsheet.worksheet("Warm Leads")
                
                row = [
                    warm_lead.get("platform", ""),
                    warm_lead.get("username", ""),
                    warm_lead.get("lead_data", {}).get("full_name", ""),
                    warm_lead.get("lead_data", {}).get("business_type", ""),
                    warm_lead.get("lead_data", {}).get("owner_name", ""),
                    warm_lead.get("conversation_link", ""),
                    warm_lead.get("status", "New"),
                    warm_lead.get("notes", "")
                ]
                
                worksheet.append_row(row)
                logger.info(f"Recorded warm lead: {username} in Google Sheets")
            except Exception as e:
                logger.error(f"Error recording warm lead in Google Sheets: {e}")
        
        # Send notification about new warm lead
        notify_warm_lead(warm_lead)
        
        return True
    
    def get_leads_to_follow_up(self):
        """Get a list of leads that need follow-up messages."""
        follow_up_delay_hours = self.config.get("messaging", {}).get("follow_up_delay_hours", 24)
        max_follow_ups = self.config.get("messaging", {}).get("max_follow_ups", 2)
        
        leads_to_follow_up = []
        current_time = datetime.now()
        
        # Process each sent message
        for message in self.leads_data["sent_messages"]:
            username = message.get("username")
            platform = message.get("platform")
            
            # Skip if we already got a response from this lead
            if any(r.get("username") == username and r.get("platform") == platform for r in self.leads_data["responses"]):
                continue
            
            # Count how many follow-ups we've already sent to this lead
            follow_up_count = sum(1 for f in self.leads_data["follow_ups"] 
                                if f.get("username") == username and f.get("platform") == platform)
            
            # Skip if we've already sent the maximum number of follow-ups
            if follow_up_count >= max_follow_ups:
                continue
            
            # Check if it's time for a follow-up
            message_time = datetime.strptime(message.get("timestamp"), "%Y-%m-%d %H:%M:%S")
            time_since_message = (current_time - message_time).total_seconds() / 3600  # Hours
            
            # If the initial message was sent more than follow_up_delay_hours ago, add to follow-up list
            if time_since_message >= follow_up_delay_hours:
                # For follow-ups beyond the first one, check the time since the last follow-up
                if follow_up_count > 0:
                    # Get the timestamp of the most recent follow-up
                    follow_ups_to_this_lead = [f for f in self.leads_data["follow_ups"] 
                                            if f.get("username") == username and f.get("platform") == platform]
                    most_recent_follow_up = max(follow_ups_to_this_lead, key=lambda x: x.get("timestamp"))
                    follow_up_time = datetime.strptime(most_recent_follow_up.get("timestamp"), "%Y-%m-%d %H:%M:%S")
                    time_since_follow_up = (current_time - follow_up_time).total_seconds() / 3600  # Hours
                    
                    if time_since_follow_up < follow_up_delay_hours:
                        continue  # Not time for another follow-up yet
                
                # Add lead to the follow-up list
                leads_to_follow_up.append({
                    "username": username,
                    "platform": platform,
                    "original_message": message.get("message"),
                    "lead_data": message.get("lead_data", {}),
                    "follow_up_count": follow_up_count + 1  # Incrementing by 1 since this will be the next follow-up
                })
        
        return leads_to_follow_up
    
    def is_positive_response(self, response_text):
        """
        Analyze a response to determine if it indicates interest (warm lead).
        Very basic implementation - in a real scenario, this would use NLP or more sophisticated analysis.
        """
        positive_indicators = [
            "interested", "tell me more", "sounds good", "price", "pricing", "cost",
            "how much", "portfolio", "examples", "website", "more info", "call",
            "phone", "talk", "discuss", "contact", "email", "send", "details"
        ]
        
        response_lower = response_text.lower()
        
        for indicator in positive_indicators:
            if indicator in response_lower:
                return True
        
        return False
    
    def export_leads_to_csv(self, filename="leads_export.csv"):
        """Export all tracked data to a CSV file."""
        try:
            # Prepare data for export
            export_data = []
            
            # Process sent messages
            for message in self.leads_data["sent_messages"]:
                username = message.get("username")
                platform = message.get("platform")
                
                # Check if this lead has responded
                has_response = any(r.get("username") == username and r.get("platform") == platform 
                                for r in self.leads_data["responses"])
                
                # Check if this lead is marked as a warm lead
                is_warm_lead = any(w.get("username") == username and w.get("platform") == platform 
                                for w in self.leads_data["warm_leads"])
                
                # Count follow-ups
                follow_up_count = sum(1 for f in self.leads_data["follow_ups"] 
                                    if f.get("username") == username and f.get("platform") == platform)
                
                # Create export record
                export_record = {
                    "Platform": message.get("platform", ""),
                    "Username": username,
                    "Business Name": message.get("lead_data", {}).get("full_name", ""),
                    "Business Type": message.get("lead_data", {}).get("business_type", ""),
                    "Owner Name": message.get("lead_data", {}).get("owner_name", ""),
                    "Initial Message": message.get("message", ""),
                    "Message Sent At": message.get("timestamp", ""),
                    "Follow Up Count": follow_up_count,
                    "Has Responded": "Yes" if has_response else "No",
                    "Is Warm Lead": "Yes" if is_warm_lead else "No",
                    "Status": "Warm Lead" if is_warm_lead else "Responded" if has_response else "Waiting"
                }
                
                export_data.append(export_record)
            
            # Create DataFrame and export to CSV
            df = pd.DataFrame(export_data)
            df.to_csv(filename, index=False)
            logger.info(f"Exported leads data to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting leads to CSV: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    tracker = LeadTracker()
    
    # Example message data
    test_message = {
        "platform": "instagram",
        "username": "test_business",
        "message": "Hey there! I noticed your business and thought you might be interested in a website.",
        "timestamp": format_timestamp(),
        "message_type": "initial",
        "lead_data": {
            "full_name": "Test Business",
            "owner_name": "John",
            "business_type": "Barber Shop"
        }
    }
    
    # Record a sent message
    tracker.record_sent_message(test_message)
    
    # Example response data
    test_response = {
        "platform": "instagram",
        "username": "test_business",
        "original_message": test_message["message"],
        "response_message": "Yes, I'm interested. What's the price?",
        "response_timestamp": format_timestamp(),
        "status": "New",
        "lead_data": test_message["lead_data"]
    }
    
    # Record a response
    tracker.record_response(test_response)
    
    # Export all data
    tracker.export_leads_to_csv() 