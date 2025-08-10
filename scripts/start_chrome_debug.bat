@echo off
echo Starting Chrome in debug mode...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome_debug_profile
echo Chrome started with debug port 9222
timeout /t 5