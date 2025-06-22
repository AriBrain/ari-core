<#
.SYNOPSIS
    This script automatically installs all necessary prerequisites (C++ Build Tools,
    pyenv-win, Python 3.10.11) and then installs the ARIBrain package.
.DESCRIPTION
    0.  Checks if the "Desktop development with C++" workload is installed,
        and if not, automatically downloads and installs it.
    1.  Checks if pyenv-win is installed and installs it if absent.
    2.  Installs Python 3.10.11, updating definitions and retrying if needed.
    3.  Installs the ARIBrain package using pipx.
#>

# Step 0: Check for and automatically install C++ Build Tools
Write-Host "Step 0: Checking for C++ Build Tools..."
# The required workload for compiling Python extensions.
$requiredWorkload = "Microsoft.VisualStudio.Workload.NativeDesktop"

# Use vswhere, the official tool for finding Visual Studio installations.
$vswherePath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$workloadInstalled = $false
if (Test-Path $vswherePath) {
    $vs_instance = & $vswherePath -products * -requires $requiredWorkload -latest
    if ($vs_instance) {
        $workloadInstalled = $true
    }
}

if ($workloadInstalled) {
    Write-Host "C++ Build Tools (Desktop development) are already installed."
} else {
    Write-Host "C++ Build Tools not found. Installing automatically..." -ForegroundColor Yellow
    Write-Host "This is a large download from Microsoft and may take a significant amount of time."

    # Download the Visual Studio Installer bootstrapper.
    $vsInstallerUrl = "https://aka.ms/vs/17/release/vs_BuildTools.exe"
    $vsInstallerPath = ".\vs_BuildTools.exe"
    Invoke-WebRequest -Uri $vsInstallerUrl -OutFile $vsInstallerPath

    # Run the installer silently from the command line.
    # It will add the required C++ workload and include recommended components.
    # The '--wait' flag ensures the script pauses until the installation is complete.
    $arguments = "--quiet --wait --norestart --nocache --add $requiredWorkload --includeRecommended"
    Start-Process -FilePath $vsInstallerPath -ArgumentList $arguments -Wait -Verb RunAs

    Write-Host "C++ Build Tools installation complete." -ForegroundColor Green
    Remove-Item $vsInstallerPath
}


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

# Step 2: Install Python if needed, with automatic retry
$pythonVersion = "3.10.11"
Write-Host "Step 2: Verifying Python $pythonVersion installation..."

$installedVersions = pyenv versions
if ($installedVersions -match $pythonVersion) {
    Write-Host "Python $pythonVersion is already installed via pyenv-win."
} else {
    Write-Host "Attempting to install Python $pythonVersion..."
    # Try to install the version directly.
    # We capture all output streams (Success, Error, etc.) to check for the specific error.
    $installOutput = pyenv install $pythonVersion 2>&1

    # If the install fails with "definition not found", update and retry.
    if ($installOutput -match "definition not found") {
        Write-Host "Definition not found. Updating pyenv-win definitions and retrying..." -ForegroundColor Yellow
        pyenv update
        Write-Host "Retrying installation of Python $pythonVersion..."
        pyenv install $pythonVersion
    }
    
    # After installing, pyenv-win requires a 'rehash'
    pyenv rehash
    
    # Verify that the installation was actually successful before proceeding.
    $recheckVersions = pyenv versions
    if ($recheckVersions -match $pythonVersion) {
        Write-Host "Python $pythonVersion has been installed successfully." -ForegroundColor Green
    } else {
        Write-Error "Failed to install Python $pythonVersion. Please review the output above for errors from pyenv."
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