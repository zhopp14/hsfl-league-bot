@echo off
cd /d "c:\Users\zacha\Downloads\League Bot"

echo ====== GIT STATUS ======
git status --short

echo.
echo ====== GIT ADD ======
git add "HSFL League Bot/cogs/sign.py"
echo Files added

echo.
echo ====== GIT COMMIT ======
git commit -m "Remove channel restriction from release and promote commands"

echo.
echo ====== GIT PUSH ======
git push origin main

echo.
echo ====== COMMIT INFO ======
git log --oneline -1

echo.
echo ====== PUSH SUCCESS ======
echo Push completed!

pause
