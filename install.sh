
#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Step 0: Check for and install compiler tools if missing
# =========================================================
if ! command -v gcc &> /dev/null; then
    echo "C/C++ compiler not found. An attempt will be made to install the required tools."

    # Check for macOS
    if [[ "$(uname)" == "Darwin" ]]; then
        echo "On macOS, Xcode Command Line Tools are required."
        echo "This script will now attempt to launch the installer."
        echo "Please follow the on-screen GUI prompts to complete the installation."
        
        # This command launches the GUI installer. The script cannot wait for it to finish.
        xcode-select --install
        
        echo ""
        echo "IMPORTANT: After the Xcode Command Line Tools installation is complete, please re-run this script to continue installing ARIBrain."
        exit 1 # Exit the script, requiring the user to run it again after the tools are installed.

    # Check for Debian/Ubuntu (uses apt)
    elif command -v apt-get &> /dev/null; then
        echo "On Debian/Ubuntu, the 'build-essential' package is required."
        read -p "Install 'build-essential' using sudo apt? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Running 'sudo apt update && sudo apt install -y build-essential'..."
            sudo apt update
            sudo apt install -y build-essential
        else
            echo "Compiler installation skipped. Please install 'build-essential' manually and re-run this script."
            exit 1
        fi

    # Check for Fedora/CentOS/RHEL (uses dnf/yum)
    elif command -v dnf &> /dev/null || command -v yum &> /dev/null; then
        echo "On Fedora/CentOS/RHEL, 'Development Tools' are required."
        read -p "Install 'Development Tools' using sudo? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v dnf &> /dev/null; then
                echo "Running 'sudo dnf groupinstall -y \"Development Tools\"'..."
                sudo dnf groupinstall -y "Development Tools"
            else
                echo "Running 'sudo yum groupinstall -y \"Development Tools\"'..."
                sudo yum groupinstall -y "Development Tools"
            fi
        else
            echo "Compiler installation skipped. Please install 'Development Tools' manually and re-run this script."
            exit 1
        fi
    else
        echo "Could not determine Linux distribution or package manager."
        echo "Please install the equivalent of 'build-essential' or 'Development Tools' for your system and re-run this script."
        exit 1
    fi
else
    echo "Compiler (gcc) found."
fi


# Step 1: Check or install pyenv
# =========================================================
if ! command -v pyenv &> /dev/null; then
  echo "Installing pyenv..."
  # Use a non-interactive install if possible
  curl https://pyenv.run | bash
fi

# Add pyenv to PATH and initialize it for the current session
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"


# Step 2: Install Python 3.10.14 if not already installed
# =========================================================
PYTHON_VERSION="3.10.14" # Define version for easy updates
if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
  echo "Installing Python ${PYTHON_VERSION} via pyenv... (This may take several minutes)"
  pyenv install "${PYTHON_VERSION}"
fi


# Step 3: Set Python version for pipx
# =========================================================
# Point pipx to the specific pyenv-managed Python executable
export PIPX_DEFAULT_PYTHON="$(pyenv root)/versions/${PYTHON_VERSION}/bin/python"


# Step 4: Use pipx to install
# =========================================================
echo "Installing ARIBrain using pipx with Python ${PYTHON_VERSION}..."
pipx install --python "$PIPX_DEFAULT_PYTHON" git+https://github.com/AriBrain/ari-core.git

echo ""
echo "✅ ARIBrain installation complete!"
echo "To run the application, type: aribrain"



# #!/bin/bash

# # Step 1: Check or install pyenv
# if ! command -v pyenv &> /dev/null; then
#   echo "Installing pyenv..."
#   curl https://pyenv.run | bash
#   export PATH="$HOME/.pyenv/bin:$PATH"
#   eval "$(pyenv init --path)"
#   eval "$(pyenv init -)"
# fi

# # Step 2: Install Python 3.10.14 if not already installed
# if ! pyenv versions --bare | grep -q "3.10.14"; then
#   echo "Installing Python 3.10.14 via pyenv..."
#   pyenv install 3.10.14
# fi

# # Step 3: Use pyenv to create a virtual environment
# export PIPX_DEFAULT_PYTHON="$(pyenv root)/versions/3.10.14/bin/python3.10"

# # Step 4: Use pipx to install
# echo "Installing ARIBrain using pipx with Python 3.10.14..."
# pipx install --python "$PIPX_DEFAULT_PYTHON" git+https://github.com/AriBrain/ari-core.git

