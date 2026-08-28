param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath
)

$ErrorActionPreference = "Stop"

$PackRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $PackRoot "repo_files"

if (-not (Test-Path $RepoPath)) {
    throw "Repository path not found: $RepoPath"
}

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    Write-Warning "No .git folder was found. Make sure RepoPath points to your cloned repository."
}

Write-Host "Backing up files that will be removed/replaced..." -ForegroundColor Cyan
$Backup = Join-Path $RepoPath "_repo_polish_backup"
New-Item -ItemType Directory -Path $Backup -Force | Out-Null

$OldFiles = @(
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "ORIGIN.md",
    "CHANGELOG_V3.md",
    "CHANGELOG_V4.md",
    "FINAL_NOTES.md"
)

foreach ($Relative in $OldFiles) {
    $Path = Join-Path $RepoPath $Relative
    if (Test-Path $Path) {
        Copy-Item $Path (Join-Path $Backup ([IO.Path]::GetFileName($Relative))) -Force
    }
}

Write-Host "Copying professional repository files..." -ForegroundColor Cyan
Copy-Item (Join-Path $Source "*") $RepoPath -Recurse -Force

Write-Host "Removing obsolete prototype documentation..." -ForegroundColor Cyan
@(
    "ORIGIN.md",
    "CHANGELOG_V3.md",
    "CHANGELOG_V4.md",
    "FINAL_NOTES.md"
) | ForEach-Object {
    $Path = Join-Path $RepoPath $_
    if (Test-Path $Path) {
        Remove-Item $Path -Force
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host ""
Write-Host "Next commands:"
Write-Host "  cd `"$RepoPath`""
Write-Host "  python -m pip install -r requirements-dev.txt"
Write-Host "  python -m compileall -q assistant tools ui scripts main.py"
Write-Host "  python -m pytest -q"
Write-Host "  git status"
