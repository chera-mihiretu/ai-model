# Exelsias - Windows Build Script
# ================================
# Complete build script for creating Windows NSIS installer
# This script builds the Python backend, React frontend, and Electron app

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Exelsias - Windows Build Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to display section header
function Write-Section {
    param($Title)
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host ""
}

# Check prerequisites
Write-Section "Checking Prerequisites"

$missingTools = @()

if (-not (Test-Command "python")) {
    $missingTools += "Python 3.10 or 3.11"
}

if (-not (Test-Command "node")) {
    $missingTools += "Node.js 18+"
}

if (-not (Test-Command "npm")) {
    $missingTools += "npm"
}

if ($missingTools.Count -gt 0) {
    Write-Host "ERROR: Missing required tools:" -ForegroundColor Red
    foreach ($tool in $missingTools) {
        Write-Host "  - $tool" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please install the missing tools and try again." -ForegroundColor Yellow
    Write-Host "See WINDOWS_BUILD_GUIDE.md for installation instructions." -ForegroundColor Yellow
    exit 1
}

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green

# Check Node version
$nodeVersion = node --version
Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green

# Check npm version
$npmVersion = npm --version
Write-Host "✓ npm: $npmVersion" -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host ""
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host "  pip install pyinstaller" -ForegroundColor White
    exit 1
}

# Clean build if requested
if ($Clean) {
    Write-Section "Cleaning Previous Builds"
    
    $cleanPaths = @(
        "story-bible-electron\backend\dist",
        "story-bible-electron\backend\build",
        "story-bible-electron\backend\dist-win",
        "story-bible-electron\frontend\dist",
        "story-bible-electron\frontend\node_modules",
        "story-bible-electron\electron\node_modules",
        "story-bible-electron\dist"
    )
    
    foreach ($path in $cleanPaths) {
        if (Test-Path $path) {
            Write-Host "Removing $path..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force $path
        }
    }
    
    Write-Host "✓ Clean completed" -ForegroundColor Green
}

# Build Python Backend
if (-not $SkipBackend) {
    Write-Section "Building Python Backend"
    
    Push-Location "story-bible-electron\backend"
    
    try {
        & ".\build-backend.ps1"
        if ($LASTEXITCODE -ne 0) {
            throw "Backend build failed"
        }
    } catch {
        Write-Host ""
        Write-Host "ERROR: Backend build failed!" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    
    Write-Host "✓ Backend build completed" -ForegroundColor Green
} else {
    Write-Host "Skipping backend build (--SkipBackend flag)" -ForegroundColor Yellow
}

# Build React Frontend
if (-not $SkipFrontend) {
    Write-Section "Building React Frontend"
    
    Push-Location "story-bible-electron\frontend"
    
    try {
        # Install dependencies if node_modules doesn't exist
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
            npm install
            if ($LASTEXITCODE -ne 0) {
                throw "npm install failed"
            }
        }
        
        # Build frontend
        Write-Host "Building frontend..." -ForegroundColor Yellow
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed"
        }
        
        # Verify output
        if (-not (Test-Path "dist\index.html")) {
            throw "Frontend build output not found"
        }
        
    } catch {
        Write-Host ""
        Write-Host "ERROR: Frontend build failed!" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    
    Write-Host "✓ Frontend build completed" -ForegroundColor Green
} else {
    Write-Host "Skipping frontend build (--SkipFrontend flag)" -ForegroundColor Yellow
}

# Build Electron App
Write-Section "Building Electron App (NSIS Installer)"

Push-Location "story-bible-electron\electron"

try {
    # Install dependencies if node_modules doesn't exist
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing Electron dependencies..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            throw "npm install failed"
        }
    }
    
    # Verify icon exists
    if (-not (Test-Path "icon.ico")) {
        Write-Host "WARNING: icon.ico not found. Using default icon." -ForegroundColor Yellow
    } else {
        Write-Host "✓ Icon file found" -ForegroundColor Green
    }
    
    # Build Electron app
    Write-Host ""
    Write-Host "Building Electron app with electron-builder..." -ForegroundColor Yellow
    Write-Host "This may take several minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    npm run build:win
    if ($LASTEXITCODE -ne 0) {
        throw "Electron build failed"
    }
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Electron build failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Verify output
Write-Section "Verifying Build Output"

$distPath = "story-bible-electron\dist"
if (-not (Test-Path $distPath)) {
    Write-Host "ERROR: Dist folder not found!" -ForegroundColor Red
    exit 1
}

# Find the installer
$installers = Get-ChildItem "$distPath\*.exe" -ErrorAction SilentlyContinue
if ($installers.Count -eq 0) {
    Write-Host "ERROR: No installer found in dist folder!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Build completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Output files:" -ForegroundColor Cyan
foreach ($installer in $installers) {
    $size = [math]::Round($installer.Length / 1MB, 2)
    Write-Host "  - $($installer.Name) ($size MB)" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Build Completed Successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installer location:" -ForegroundColor Yellow
Write-Host "  $distPath" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the installer on a clean Windows machine" -ForegroundColor White
Write-Host "  2. Verify both TTS and LLM functionality work" -ForegroundColor White
Write-Host "  3. Check that the model loading feature works" -ForegroundColor White
Write-Host ""
Write-Host "See WINDOWS_BUILD_GUIDE.md for testing instructions." -ForegroundColor Cyan
Write-Host ""
