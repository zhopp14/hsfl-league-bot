Push-Location "C:\Users\zacha\Downloads\League Bot\HSFL League Bot"

Write-Host "Checking git status..."
git status

Write-Host "`nAdding changes..."
git add utils/signing_tools.py

Write-Host "`nCommitting changes..."
git commit -m "Fix channel configuration type mismatch bug

- Convert channel IDs to strings when storing in database for consistency
- Convert channel IDs back to integers when retrieving from database
- Fix set_channel_config() to properly detect duplicate channels
- Fix remove_channel_config() to properly remove channels
- Fix get_channel_config() to return integers instead of strings
- Fix get_all_channel_config() to return integers for all channel IDs

This fixes the issue where /channel set command was not working because
integer channel IDs were not matching string IDs stored in the database."

Write-Host "`nPushing to GitHub..."
git push

Write-Host "`nDone!"
Pop-Location
