@echo off
cd /d E:\Generate-autounattendxml-files-for-Windows11\WebUI\frontend

echo Installing dependencies...
call npm install

echo.
echo Starting frontend server...
echo URL: http://192.168.3.92:3050
echo.
echo Press Ctrl+C to stop
echo.

set NEXT_PUBLIC_API_URL=http://192.168.3.92:8080/api
set NEXT_PUBLIC_LOCAL_IP=192.168.3.92

call npm run dev