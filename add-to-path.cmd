@echo off
rem Adds this folder to the user PATH, so whisper-transcribe works from any folder.
rem Double-click it once. Open a new terminal afterwards.
setlocal
set "TARGET=%~dp0"
if "%TARGET:~-1%"=="\" set "TARGET=%TARGET:~0,-1%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t = $env:TARGET; $p = [Environment]::GetEnvironmentVariable('Path', 'User'); $parts = @($p -split ';' | Where-Object { $_ -ne '' }); if ($parts -contains $t) { 'Already in the user PATH: ' + $t } else { [Environment]::SetEnvironmentVariable('Path', (($parts + $t) -join ';'), 'User'); 'Added to the user PATH: ' + $t }"

echo.
echo Open a new terminal, then run: whisper-transcribe
pause
endlocal
