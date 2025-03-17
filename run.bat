@echo off
echo ===================================
echo Lead Generation Bot
echo ===================================

if "%1"=="" (
    echo Running in schedule mode...
    python main.py --action schedule
    goto end
)

if "%1"=="collect" (
    echo Running lead collection...
    python main.py --action collect --platform %2 --max_leads %3
    goto end
)

if "%1"=="message" (
    echo Sending initial messages...
    python main.py --action message --platform %2 --max_leads %3 --max_dms %4
    goto end
)

if "%1"=="follow_up" (
    echo Sending follow-up messages...
    python main.py --action follow_up --platform %2
    goto end
)

if "%1"=="run_all" (
    echo Running complete workflow...
    python main.py --action run_all
    goto end
)

echo Unknown command: %1
echo Available commands:
echo   run.bat                - Run in schedule mode
echo   run.bat collect [platform] [max_leads] - Collect leads
echo   run.bat message [platform] [max_leads] [max_dms] - Send initial messages
echo   run.bat follow_up [platform] - Send follow-up messages
echo   run.bat run_all       - Run complete workflow

:end 