@echo off
rem Scheduled run: /weekly in the research-planner folder (registered by schedule_windows.ps1).
rem ASCII only on purpose: cmd.exe reads .cmd files in the console code page (cp949 on Korean Windows).
setlocal
cd /d "%~dp0.."
rem Task Scheduler may start with a shorter PATH. Add the native installer location if claude is missing.
where claude >nul 2>nul || set "PATH=%USERPROFILE%\.local\bin;%PATH%"
rem Tells session_end_queue.py not to queue this unattended session.
set RP_SCHEDULED=1
if not exist logs mkdir logs
rem On Windows the PowerShell tool is the primary shell, so allow python in both PowerShell and Bash.
call claude -p "/weekly" --permission-mode acceptEdits --allowedTools "PowerShell(python *)" "PowerShell(py *)" "Bash(python *)" "Bash(py *)" WebFetch WebSearch > logs\schedule-weekly.log 2>&1
endlocal
