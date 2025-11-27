@echo off
cd /d "c:\Users\zacha\Downloads\League Bot"
echo ===== GIT STATUS ===== > push_log.txt
git status --short >> push_log.txt 2>&1
echo. >> push_log.txt
echo ===== GIT LOG ===== >> push_log.txt
git log --oneline -2 >> push_log.txt 2>&1
echo. >> push_log.txt
echo ===== ADDING FILES ===== >> push_log.txt
git add "HSFL League Bot/cogs/sign.py" >> push_log.txt 2>&1
echo. >> push_log.txt
echo ===== COMMITTING ===== >> push_log.txt
git commit -m "Remove channel restriction from release and promote commands" >> push_log.txt 2>&1
echo. >> push_log.txt
echo ===== PUSHING ===== >> push_log.txt
git push >> push_log.txt 2>&1
echo. >> push_log.txt
echo ===== FINAL LOG ===== >> push_log.txt
git log --oneline -2 >> push_log.txt 2>&1
