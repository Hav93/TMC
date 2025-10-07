param([Parameter(Mandatory=$true)][string]$NewVersion)

Write-Host ""
Write-Host "========================================"
Write-Host " TMC Version Update Tool"
Write-Host "========================================"
Write-Host ""
Write-Host "Target Version: $NewVersion"
Write-Host ""

if ($NewVersion -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "[ERROR] Invalid version format" -ForegroundColor Red
    Write-Host "Correct format: X.Y.Z (e.g. 1.2.0)" -ForegroundColor Yellow
    exit 1
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[1/3] Updating VERSION file..."
# 保存为无 BOM 的 UTF-8
[System.IO.File]::WriteAllText("$PWD\VERSION", $NewVersion, (New-Object System.Text.UTF8Encoding $false))
Write-Host "      Done"
Write-Host ""

Write-Host "[2/3] Syncing package.json..."
$result = node scripts/sync-version.js 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "      $result"
} else {
    Write-Host "      [ERROR] $result" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[3/3] Environment check..."
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "      Python installed"
} else {
    Write-Host "      [WARN] Python not found" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================"
Write-Host " Version Updated Successfully"
Write-Host "========================================"
Write-Host ""
Write-Host "Updated files:"
Write-Host "  - VERSION"
Write-Host "  - app/frontend/package.json"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Update CHANGELOG.md"
Write-Host "  2. Update README.md"
Write-Host "  3. Update DEPLOYMENT.md"
Write-Host "  4. Commit and tag:"
Write-Host "     git add ."
Write-Host "     git commit -m 'chore: bump version to $NewVersion'"
Write-Host "     git tag v$NewVersion"
Write-Host "     git push"
Write-Host "     git push --tags"
Write-Host ""
