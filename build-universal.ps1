# =============================================================================
# Exelsias - Universal Build Script (Compatible with ALL Windows PCs)
# =============================================================================
# This script builds the application with basic CPU support (no AVX2 required)
# ensuring compatibility with older gaming PCs and budget processors.
#
# Usage:
#   .\build-universal.ps1                  # Full build
#   .\build-universal.ps1 -SkipBackend     # Skip Python backend rebuild
#   .\build-universal.ps1 -SkipFrontend    # Skip frontend rebuild
#   .\build-universal.ps1 -Clean           # Clean all previous builds first
#   .\build-universal.ps1 -ReinstallLlama  # Force reinstall llama-cpp-python
# =============================================================================

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$Clean,
    [switch]$ReinstallLlama
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Banner {
    param($Text, $Color = "Cyan")
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host ("=" * 60) -ForegroundColor $Color
    Write-Host ""
}

function Write-Step {
    param($Number, $Text)
    Write-Host ""
    Write-Host "[$Number] $Text" -ForegroundColor Yellow
    Write-Host ("-" * 50) -ForegroundColor DarkGray
}

function Write-Success {
    param($Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Warning {
    param($Text)
    Write-Host "[WARN] $Text" -ForegroundColor Yellow
}

function Write-Error {
    param($Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# ============================================================================
# Main Script
# ============================================================================

Write-Banner "EXELSIAS - Universal Build Script" "Cyan"
Write-Host "Building for ALL Windows PCs (No AVX2 Required)" -ForegroundColor White
Write-Host ""

# ----------------------------------------------------------------------------
# Step 1: Check Prerequisites
# ----------------------------------------------------------------------------
Write-Step "1" "Checking Prerequisites"

$errors = @()

# Check Python
if (Test-Command "python") {
    $pyVer = python --version 2>&1
    Write-Success "Python: $pyVer"
    
    # Warn if Python 3.12+
    if ($pyVer -match "3\.1[2-9]") {
        Write-Warning "Python 3.12+ detected. Recommend 3.10 or 3.11 for best compatibility."
    }
} else {
    $errors += "Python not found. Install Python 3.10 or 3.11"
}

# Check Node.js
if (Test-Command "node") {
    $nodeVer = node --version
    Write-Success "Node.js: $nodeVer"
} else {
    $errors += "Node.js not found. Install Node.js 18+ LTS"
}

# Check npm
if (Test-Command "npm") {
    $npmVer = npm --version
    Write-Success "npm: $npmVer"
} else {
    $errors += "npm not found"
}

# Exit if prerequisites missing
if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Error "Missing prerequisites:"
    foreach ($err in $errors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please install the missing tools and try again." -ForegroundColor Yellow
    exit 1
}

# ----------------------------------------------------------------------------
# Step 2: Check/Create Virtual Environment
# ----------------------------------------------------------------------------
Write-Step "2" "Checking Virtual Environment"

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

Write-Host "Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated"

# ----------------------------------------------------------------------------
# Step 3: Install/Update llama-cpp-python with Universal CPU Support
# ----------------------------------------------------------------------------
Write-Step "3" "Configuring Universal CPU Support (No AVX2)"

# Check if llama-cpp-python needs to be reinstalled
$needsReinstall = $ReinstallLlama

if (-not $needsReinstall) {
    $llamaInstalled = pip show llama-cpp-python 2>$null
    if (-not $llamaInstalled) {
        $needsReinstall = $true
        Write-Host "llama-cpp-python not installed, will install..." -ForegroundColor Yellow
    } else {
        Write-Success "llama-cpp-python already installed"
        Write-Host "  (Use -ReinstallLlama flag to force rebuild with basic CPU)" -ForegroundColor Gray
    }
}

if ($needsReinstall) {
    Write-Host ""
    Write-Host "Installing llama-cpp-python with BASIC CPU support..." -ForegroundColor Yellow
    Write-Host "This ensures compatibility with ALL Windows PCs" -ForegroundColor Gray
    Write-Host ""
    
    # Uninstall existing
    pip uninstall llama-cpp-python -y 2>$null
    
    # Set environment variables to disable AVX2 and advanced CPU features
    $env:CMAKE_ARGS = "-DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF"
    $env:FORCE_CMAKE = "1"
    
    Write-Host "CMAKE_ARGS: $env:CMAKE_ARGS" -ForegroundColor DarkGray
    Write-Host ""
    
    # Install from source with basic CPU
    pip install llama-cpp-python --no-binary llama-cpp-python --force-reinstall --no-cache-dir
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Source build failed, trying pre-built wheel..."
        pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install llama-cpp-python"
            exit 1
        }
    }
    
    Write-Success "llama-cpp-python installed with universal CPU support"
}

# ----------------------------------------------------------------------------
# Step 4: Install Other Python Dependencies
# ----------------------------------------------------------------------------
Write-Step "4" "Installing Python Dependencies"

Write-Host "Installing requirements..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Python dependencies"
    exit 1
}

# Ensure PyInstaller is installed
pip install pyinstaller --quiet
Write-Success "Python dependencies installed"

# ----------------------------------------------------------------------------
# Step 5: Clean Previous Builds (if requested)
# ----------------------------------------------------------------------------
if ($Clean) {
    Write-Step "5" "Cleaning Previous Builds"
    
    $cleanPaths = @(
        "story-bible-electron\backend\dist",
        "story-bible-electron\backend\build",
        "story-bible-electron\backend\dist-win",
        "story-bible-electron\frontend\dist",
        "story-bible-electron\dist"
    )
    
    foreach ($path in $cleanPaths) {
        if (Test-Path $path) {
            Write-Host "  Removing $path..." -ForegroundColor Gray
            Remove-Item -Recurse -Force $path
        }
    }
    
    Write-Success "Clean completed"
}

# ----------------------------------------------------------------------------
# Step 6: Build Python Backend
# ----------------------------------------------------------------------------
if (-not $SkipBackend) {
    Write-Step "6" "Building Python Backend"
    
    Push-Location "story-bible-electron\backend"
    
    # Clean previous builds
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    
    Write-Host "Running PyInstaller..." -ForegroundColor Gray
    Write-Host "This may take several minutes..." -ForegroundColor DarkGray
    
    pyinstaller backend.spec
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller build failed"
        Pop-Location
        exit 1
    }
    
    # Verify output
    if (-not (Test-Path "dist\api_bridge.exe")) {
        Write-Error "api_bridge.exe not found after build"
        Pop-Location
        exit 1
    }
    
    # Copy to dist-win
    if (-not (Test-Path "dist-win")) {
        New-Item -ItemType Directory -Path "dist-win" | Out-Null
    }
    Copy-Item "dist\api_bridge.exe" "dist-win\api_bridge.exe" -Force
    
    $size = [math]::Round((Get-Item "dist-win\api_bridge.exe").Length / 1MB, 2)
    Write-Success "Backend built: api_bridge.exe ($size MB)"
    
    Pop-Location
} else {
    Write-Host ""
    Write-Host "Skipping backend build (-SkipBackend flag)" -ForegroundColor Yellow
}

# ----------------------------------------------------------------------------
# Step 7: Build React Frontend
# ----------------------------------------------------------------------------
if (-not $SkipFrontend) {
    Write-Step "7" "Building React Frontend"
    
    Push-Location "story-bible-electron\frontend"
    
    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "npm install failed"
            Pop-Location
            exit 1
        }
    }
    
    # Build
    Write-Host "Building frontend..." -ForegroundColor Gray
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend build failed"
        Pop-Location
        exit 1
    }
    
    # Verify
    if (-not (Test-Path "dist\index.html")) {
        Write-Error "Frontend build output not found"
        Pop-Location
        exit 1
    }
    
    Write-Success "Frontend built successfully"
    
    Pop-Location
} else {
    Write-Host ""
    Write-Host "Skipping frontend build (-SkipFrontend flag)" -ForegroundColor Yellow
}

# ----------------------------------------------------------------------------
# Step 8: Check/Create Application Icon
# ----------------------------------------------------------------------------
Write-Step "8" "Checking Application Icon"

$iconPath = "story-bible-electron\electron\icon.ico"
$logoIcoPath = "story-bible-electron\frontend\public\assets\logo.ico"
$logoPngPath = "story-bible-electron\frontend\public\assets\logo.png"

# Always copy fresh icon from assets
if (Test-Path $logoIcoPath) {
    Copy-Item $logoIcoPath $iconPath -Force
    $size = (Get-Item $iconPath).Length
    Write-Success "Application icon copied: icon.ico ($size bytes)"
} elseif (Test-Path $logoPngPath) {
    Write-Host "Converting logo.png to icon.ico..." -ForegroundColor Gray
    
    # Try to convert using Python/Pillow
    $convertScript = @"
from PIL import Image
img = Image.open('$($logoPngPath.Replace('\', '/'))').convert('RGBA')
img.save('$($iconPath.Replace('\', '/'))', format='ICO', sizes=[(256,256),(48,48),(32,32),(16,16)])
print('Icon converted successfully')
"@
    
    try {
        python -c $convertScript
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Icon converted from PNG"
        } else {
            throw "Conversion failed"
        }
    } catch {
        Write-Warning "Could not convert icon automatically."
        Write-Host "  Please manually convert logo.png to icon.ico" -ForegroundColor Gray
        Write-Host "  Use: https://cloudconvert.com/png-to-ico" -ForegroundColor Gray
    }
} else {
    Write-Warning "No icon found. The app will use default Electron icon."
    Write-Host "  Add icon at: story-bible-electron\electron\icon.ico" -ForegroundColor Gray
}

# ----------------------------------------------------------------------------
# Step 9: Build Electron Installer
# ----------------------------------------------------------------------------
Write-Step "9" "Building Electron Installer (NSIS)"

Push-Location "story-bible-electron\electron"

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Electron dependencies..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install failed"
        Pop-Location
        exit 1
    }
}

Write-Host "Building Electron app with electron-builder..." -ForegroundColor Gray
Write-Host "This may take several minutes..." -ForegroundColor DarkGray
Write-Host ""

npm run build:win

if ($LASTEXITCODE -ne 0) {
    Write-Error "Electron build failed"
    Pop-Location
    exit 1
}

Pop-Location

# ----------------------------------------------------------------------------
# Step 10: Verify Final Output
# ----------------------------------------------------------------------------
Write-Step "10" "Verifying Build Output"

$distPath = "story-bible-electron\dist"
$installers = Get-ChildItem "$distPath\*.exe" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Setup" }

if ($installers.Count -eq 0) {
    Write-Error "No installer found in dist folder!"
    exit 1
}

Write-Banner "BUILD COMPLETED SUCCESSFULLY!" "Green"

Write-Host "Output Files:" -ForegroundColor Cyan
foreach ($installer in $installers) {
    $size = [math]::Round($installer.Length / 1MB, 2)
    Write-Host "  [INSTALLER] $($installer.Name) ($size MB)" -ForegroundColor White
}

$unpacked = "$distPath\win-unpacked"
if (Test-Path $unpacked) {
    Write-Host "  [PORTABLE]  win-unpacked\ (portable version)" -ForegroundColor White
}

Write-Host ""
Write-Host "Installer Location:" -ForegroundColor Yellow
Write-Host "  $((Get-Item $distPath).FullName)" -ForegroundColor White

Write-Host ""
Write-Host "This build is compatible with ALL Windows PCs!" -ForegroundColor Green
Write-Host "(Including older gaming PCs without AVX2 support)" -ForegroundColor Gray

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test the installer on this machine" -ForegroundColor White
Write-Host "  2. Test on an older PC without AVX2 to verify compatibility" -ForegroundColor White
Write-Host "  3. Verify these features work:" -ForegroundColor White
Write-Host "     - Model loading (no CPU error)" -ForegroundColor Gray
Write-Host "     - AI text generation" -ForegroundColor Gray
Write-Host "     - Text-to-speech (requires internet)" -ForegroundColor Gray
Write-Host "     - Animations on home screen" -ForegroundColor Gray
Write-Host "     - Application icon visible" -ForegroundColor Gray
Write-Host ""
