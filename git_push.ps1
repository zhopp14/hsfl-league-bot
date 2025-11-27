Set-Location 'c:\Users\zacha\Downloads\League Bot'
$output = @()
$output += "Current directory: $(Get-Location)"
$output += "Git status:"
$output += (git status --short 2>&1)
$output += ""
$output += "Git log (last 2):"
$output += (git log --oneline -2 2>&1)
$output += ""
$output += "Pushing to GitHub..."
$output += (git push 2>&1)
$output += "Push complete"
$output -join "`n" | Out-File "c:\Users\zacha\Downloads\League Bot\git_output.txt" -Encoding utf8
Write-Host ($output -join "`n")
