# Build Python Backend with PyInstaller for Windows
# ===================================================
# This script bundles the Python backend into a standalone executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Python Backend for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "..\..\venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  cd ..\.." -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Yellow
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "..\..\venv\Scripts\Activate.ps1"

# Check if PyInstaller is installed
Write-Host "Checking PyInstaller..." -ForegroundColor Green
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous build
if (Test-Path "dist") {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

# Run PyInstaller
Write-Host ""
Write-Host "Running PyInstaller..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

pyinstaller backend.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: PyInstaller build failed!" -ForegroundColor Red
    Write-Host "Check the output above for errors." -ForegroundColor Yellow
    exit 1
}

# Verify output
if (-not (Test-Path "dist\api_bridge.exe")) {
    Write-Host ""
    Write-Host "ERROR: api_bridge.exe not found in dist folder!" -ForegroundColor Red
    exit 1
}

# Create dist-win folder if it doesn't exist
if (-not (Test-Path "dist-win")) {
    New-Item -ItemType Directory -Path "dist-win" | Out-Null
}

# Copy the executable
Write-Host ""
Write-Host "Copying executable to dist-win..." -ForegroundColor Green
Copy-Item "dist\api_bridge.exe" "dist-win\api_bridge.exe" -Force

# Verify DLLs are included
Write-Host "Verifying build..." -ForegroundColor Green
$fileSize = (Get-Item "dist-win\api_bridge.exe").Length / 1MB
Write-Host "  Executable size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan

# Check for common DLLs in the dist folder
$dllCount = (Get-ChildItem "dist" -Filter "*.dll" -Recurse).Count
if ($dllCount -gt 0) {
    Write-Host "  Found $dllCount DLL files" -ForegroundColor Cyan
} else {
    Write-Host "  WARNING: No DLL files found. This may cause runtime errors." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output: story-bible-electron\backend\dist-win\api_bridge.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Build the frontend: cd ..\frontend && npm run build" -ForegroundColor White
Write-Host "  2. Build Electron app: cd ..\electron && npm run build:win" -ForegroundColor White
Write-Host ""
