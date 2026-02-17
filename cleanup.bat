@echo off
echo ==========================================
echo   WAIFUGEN - SYSTEM CLEANUP TOOL
echo ==========================================
echo.
echo WARNING: This will remove:
echo  - Stopped containers
echo  - Unused networks
echo  - Unused images (dangling)
echo  - Build cache
echo.
echo This releases A LOT of disk space and memory.
echo Your active services (N8N, Postgres) will NOT be touched.
echo.
pause

echo.
echo Cleaning up...
docker system prune -f

echo.
echo Checking for old images...
docker image prune -f

echo.
echo [SUCCESS] Cleanup Complete!
echo You can now run Start_Service.bat perfectly.
echo.
pause
