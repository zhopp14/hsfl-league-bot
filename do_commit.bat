@echo off
cd /d "c:\Users\zacha\Downloads\League Bot"
echo === Git Status ===
git status --short
echo.
echo === Adding changes ===
git add -A
echo.
echo === Committing ===
git commit -m "Remove channel restriction from release and promote commands"
echo.
echo === Pushing ===
git push
echo.
echo === Done ===
