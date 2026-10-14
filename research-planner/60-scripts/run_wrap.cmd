@echo off
rem Scheduled run: /wrap in the research-planner folder (registered by schedule_windows.ps1).
rem ASCII only on purpose: cmd.exe reads .cmd files in the console code page (cp949 on Korean Windows).
setlocal
cd /d "%~dp0.."
rem Task Scheduler may start with a shorter PATH. Add the native installer location if claude is missing.
where claude >nul 2>nul || set "PATH=%USERPROFILE%\.local\bin;%PATH%"
rem Tells session_end_queue.py not to queue this unattended session.
set RP_SCHEDULED=1
if not exist logs mkdir logs
rem acceptEdits covers file edits, but not PowerShell Move-Item/New-Item, so allow the queue moves explicitly.
call claude -p "/wrap" --permission-mode acceptEdits --allowedTools "PowerShell(Move-Item *)" "PowerShell(New-Item *)" "Bash(mv *)" "Bash(mkdir *)" > logs\schedule-wrap.log 2>&1
endlocal
