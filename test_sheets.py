import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("Starting Google Sheets test...")

try:
    # Set up the credentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)
    client = gspread.authorize(credentials)
    
    print("Successfully authenticated with Google API")
    
    # Try to open the spreadsheet
    spreadsheet_id = '1XpjF8XXXsJoZ5lSc8tAJaCUyUUlB3qddN-4bJUrUrZk'
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"Successfully opened spreadsheet: {spreadsheet.title}")
        
        # List all worksheets
        worksheets = spreadsheet.worksheets()
        print(f"Spreadsheet has {len(worksheets)} worksheets:")
        existing_worksheets = []
        for worksheet in worksheets:
            print(f"  - {worksheet.title}")
            existing_worksheets.append(worksheet.title)
        
        # Create necessary worksheets if they don't exist
        required_worksheets = ["Sent Messages", "Responses", "Follow Ups", "Warm Leads"]
        
        for name in required_worksheets:
            if name not in existing_worksheets:
                print(f"Creating worksheet: {name}")
                spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
                worksheet = spreadsheet.worksheet(name)
                
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
                print(f"Added headers to worksheet: {name}")
            else:
                print(f"Worksheet already exists: {name}")
        
        # List worksheets again to confirm
        print("\nUpdated worksheet list:")
        for worksheet in spreadsheet.worksheets():
            print(f"  - {worksheet.title}")
            
    except gspread.exceptions.APIError as e:
        print(f"API Error accessing spreadsheet: {e}")
    except Exception as e:
        print(f"Error accessing spreadsheet: {e}")
        
except Exception as e:
    print(f"Error in setup: {e}") 