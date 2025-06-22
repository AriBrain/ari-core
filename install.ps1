<#
.SYNOPSIS
    This script automatically installs pyenv-win if needed, ensures Python 3.10.14
    is installed, and then installs the ARIBrain package in an isolated
    environment using pipx.
.DESCRIPTION
    1.  Checks if pyenv-win is installed. If not, it automatically downloads,
        installs, and configures it for the current session.
    2.  Updates pyenv-win's list of available Python versions.
    3.  Checks if Python 3.10.14 is already installed. If not, it installs it
        and verifies the installation was successful.
    4.  Uses pipx to install ARIBrain from its git repository, forcing it to use
        the isolated Python 3.10.14 interpreter.
#>

# Step 1: Check for and automatically install pyenv-win
Write-Host "Step 1: Checking for pyenv-win..."
if (-not (Get-Command pyenv -ErrorAction SilentlyContinue)) {
    Write-Host "pyenv-win not found. Installing it automatically..." -ForegroundColor Yellow

    # Download and execute the official installer script
    $installerPath = ".\install-pyenv-win.ps1"
    Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile $installerPath
    & $installerPath

    Write-Host "pyenv-win has been installed. Refreshing environment for current session..."

    # The installer modifies User-level environment variables, but these changes
    # are not reflected in the current session. We must manually update them.
    $env:PYENV_ROOT = [System.Environment]::GetEnvironmentVariable('PYENV_ROOT', 'User')
    $env:PYENV_HOME = [System.Environment]::GetEnvironmentVariable('PYENV_HOME', 'User')
    
    # Prepend the pyenv paths to the current session's PATH variable
    $pyenvBinPath = Join-Path -Path $env:PYENV_HOME -ChildPath "bin"
    $pyenvShimsPath = Join-Path -Path $env:PYENV_HOME -ChildPath "shims"
    $env:Path = "$pyenvBinPath;$pyenvShimsPath;" + $env:Path

    Write-Host "Environment refreshed. pyenv command is now available." -ForegroundColor Green

    # Clean up the downloaded installer
    Remove-Item $installerPath
} else {
    Write-Host "pyenv-win is already installed."
}

# Step 2: Update definitions and install Python if needed
$pythonVersion = "3.10.14"
Write-Host "Step 2: Verifying Python $pythonVersion installation..."

# [NEW] Update pyenv-win's list of available python versions to prevent "definition not found" errors.
Write-Host "Updating pyenv-win version definitions..."
pyenv update

# Check if the target version is already installed
$installedVersions = pyenv versions
if ($installedVersions -match $pythonVersion) {
    Write-Host "Python $pythonVersion is already installed via pyenv-win."
} else {
    Write-Host "Installing Python $pythonVersion via pyenv-win... (This may take a few minutes)"
    # Install the desired python version
    pyenv install $pythonVersion
    
    # After installing a new version of Python, pyenv-win requires a 'rehash'
    pyenv rehash
    
    # [IMPROVED] Verify that the installation was actually successful before proceeding.
    $recheckVersions = pyenv versions
    if ($recheckVersions -match $pythonVersion) {
        Write-Host "Python $pythonVersion has been installed successfully." -ForegroundColor Green
    } else {
        Write-Error "Failed to install Python $pythonVersion. Please run 'pyenv install $pythonVersion' manually to see the underlying error."
        exit 1 # Exit the script because subsequent steps would fail.
    }
}

# Step 3 & 4: Use pipx to install ARIBrain in an isolated environment
Write-Host "Step 3 & 4: Installing ARIBrain using pipx with Python $pythonVersion..."

# Construct the full path to the python.exe interpreter managed by pyenv-win.
$pythonPath = Join-Path -Path $env:PYENV_ROOT -ChildPath "versions\$pythonVersion\python.exe"

# Verify the Python executable exists before trying to use it.
if (-not (Test-Path $pythonPath)) {
    Write-Error "Could not find the Python executable at '$pythonPath'. Please check your pyenv-win installation."
    exit 1
}

Write-Host "Using Python interpreter at: $pythonPath"

# Use pipx to install the package.
pipx install --python $pythonPath git+https://github.com/AriBrain/ari-core.git

Write-Host "Installation complete." -ForegroundColor Green