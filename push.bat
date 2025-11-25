@echo off
cd /d "C:\Users\zacha\Downloads\League Bot\HSFL League Bot"
git add utils\signing_tools.py
git commit -m "Fix channel configuration type mismatch bug - convert channel IDs to strings when storing in database for consistency"
git push
