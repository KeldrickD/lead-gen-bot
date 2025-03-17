import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up the credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)
client = gspread.authorize(credentials)

# Open spreadsheet and print summary
spreadsheet_id = '1XpjF8XXXsJoZ5lSc8tAJaCUyUUlB3qddN-4bJUrUrZk'
spreadsheet = client.open_by_key(spreadsheet_id)

print(f"Spreadsheet: {spreadsheet.title}")

for sheet in spreadsheet.worksheets():
    values = sheet.get_all_values()
    print(f"\nSheet: {sheet.title}")
    print(f"Total rows: {len(values)}")
    
    if len(values) > 0:
        headers = values[0]
        print(f"Headers: {', '.join(headers)}")
        
        if len(values) > 1:
            print(f"Data rows: {len(values) - 1}")
            
            # Print the first data row as sample
            if len(values) > 1:
                sample_row = values[1]
                print("\nSample data row:")
                for i, header in enumerate(headers):
                    if i < len(sample_row):
                        print(f"  {header}: {sample_row[i]}")
    
    print("-" * 50) 