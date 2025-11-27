Set-Location 'c:\Users\zacha\Downloads\League Bot'

Write-Host "=== Current Status ===" -ForegroundColor Green
$status = & git status --porcelain 2>&1
if ($status) {
    Write-Host "Uncommitted changes found:"
    Write-Host $status
    Write-Host ""
    Write-Host "=== Adding and committing ===" -ForegroundColor Yellow
    & git add -A
    & git commit -m "Remove channel restriction from release and promote commands"
    Write-Host ""
    Write-Host "=== Pushing ===" -ForegroundColor Yellow
    & git push
} else {
    Write-Host "No uncommitted changes - checking if already pushed..."
}

Write-Host ""
Write-Host "=== Latest commits ===" -ForegroundColor Green
& git log --oneline -3

Write-Host ""
Write-Host "=== Remote status ===" -ForegroundColor Green
& git status
