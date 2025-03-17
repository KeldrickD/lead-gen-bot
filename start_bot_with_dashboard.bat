@echo off
echo Starting LeadGen Bot with Dashboard...

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install required packages if needed
pip install -r requirements.txt

:: Start the bot with dashboard and scheduler
start cmd /k "python main.py --action dashboard"

:: Start the scheduler in another window
start cmd /k "python main.py --action schedule"

echo Bot started with dashboard. You can access it at http://localhost:5000

:: Wait for user input before closing
pause 