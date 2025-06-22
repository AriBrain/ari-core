# Windows installation script for ARIBrain (PowerShell)
# Assumes pipx and Python 3.10.14 are already installed by the user

# Step 1: Locate Python 3.10.14 executable from pyenv or global install
# If pyenv-win is used, adapt path accordingly
$pythonPath = "$env:USERPROFILE\.pyenv\pyenv-win\versions\3.10.14\python.exe"

if (-Not (Test-Path $pythonPath)) {
    Write-Host "Python 3.10.14 not found in pyenv-win default location."
    Write-Host "Falling back to global Python installation."

    # Attempt to locate via py launcher
    $pythonCheck = & py -3.10 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python 3.10.14 not found. Please install it manually before running this script."
        exit 1
    }
    $pythonPath = $pythonCheck.Trim()
}

# Step 2: Install ARIBrain using pipx
Write-Host "Installing ARIBrain using pipx and Python at $pythonPath..."
pipx install --python "$pythonPath" git+https://github.com/AriBrain/ari-core.git