@echo off
setlocal

echo [DEPRECATED] start_api_server.bat now launches the full stack.
echo [DEPRECATED] Please use start_all_servers.bat going forward.
call "%~dp0start_all_servers.bat"

endlocal
