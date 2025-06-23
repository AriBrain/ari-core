
#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Function to check if a command exists
# --- Helper Functions ---
command_exists() {
    command -v "$1" &> /dev/null
}

# macOS: Check and install Xcode Command Line Tools and Homebrew packages
install_macos_deps() {
    echo "Checking for macOS dependencies..."

    # 1. Check for Xcode Command Line Tools (provides C compiler)
    if ! xcode-select -p &> /dev/null; then
        echo "Xcode Command Line Tools not found. They are required to compile Python."
        echo "This script will now attempt to launch the installer."
        echo "Please follow the on-screen GUI prompts to complete the installation."
        
        # This command launches the GUI installer. The script cannot wait for it to finish.
        xcode-select --install
        
        echo ""
        echo "IMPORTANT: After the Xcode Command Line Tools installation is complete, please re-run this script to continue installing ARIBrain."
        exit 1
    fi

    # 2. Check for Homebrew and other dependencies
    if ! command_exists brew; then
        echo "Warning: Homebrew not found. Cannot install recommended Python build dependencies (like openssl, xz)."
        echo "Python installation might fail or be incomplete."
        read -p "Install Homebrew now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            # Add brew to path for this session
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo "Skipping Homebrew installation. Please install it manually from https://brew.sh and re-run this script."
            exit 1
        fi
    fi
    
    local required_deps=(openssl readline sqlite3 xz zlib bzip2)
    local missing_deps=()
    echo "Checking for required Homebrew packages..."
    for dep in "${required_deps[@]}"; do
        # `brew --prefix` is a reliable way to check if a formula is installed
        brew --prefix "$dep" &> /dev/null || missing_deps+=("$dep")
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "The following recommended Python build dependencies are missing:"
        echo "  ${missing_deps[*]}"
        read -p "Install them now using Homebrew? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Installing dependencies with: brew install ${missing_deps[*]}"
            brew install "${missing_deps[@]}"
        else
            echo "Dependency installation skipped. Cannot guarantee a successful Python build."
            echo "Please install them manually ('brew install ${missing_deps[*]}') and re-run the script."
            exit 1
        fi
    fi
    echo "All macOS dependencies are met."
}

# Debian/Ubuntu: Check and install required packages
install_debian_deps() {
    echo "Checking for Debian/Ubuntu dependencies..."
    local required_deps=(build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev)
    local missing_deps=()
    for dep in "${required_deps[@]}"; do
        # Use dpkg-query to check if a package is installed
        dpkg-query -W -f='${Status}' "$dep" 2>/dev/null | grep -q "ok installed" || missing_deps+=("$dep")
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "The following required Python build dependencies are missing:"
        echo "  ${missing_deps[*]}"
        read -p "Install them now using sudo apt? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Updating package list and installing dependencies..."
            sudo apt-get update
            sudo apt-get install -y "${missing_deps[@]}"
        else
            echo "Dependency installation skipped. Cannot guarantee a successful Python build."
            echo "Please install them manually and re-run the script."
            exit 1
        fi

    fi
    echo "All Debian/Ubuntu dependencies are met."
}

# Fedora/RHEL: Check and install required packages
install_fedora_deps() {
    echo "Checking for Fedora/RHEL dependencies..."
    local required_deps=(gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel)
    local missing_deps=()
    for dep in "${required_deps[@]}"; do
        rpm -q "$dep" &> /dev/null || missing_deps+=("$dep")
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "The following required Python build dependencies are missing:"
        echo "  ${missing_deps[*]}"
        read -p "Install 'Development Tools' using sudo? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command_exists dnf; then
                sudo dnf install -y "${missing_deps[@]}"
            else
                sudo yum install -y "${missing_deps[@]}"
            fi
        else
            echo "Dependency installation skipped. Cannot guarantee a successful Python build."
            echo "Please install them manually and re-run the script."
            exit 1
        fi
    fi
    echo "All Fedora/RHEL dependencies are met."
}


# --- Main Script ---

# Step 0: Check and install system dependencies
# =========================================================
echo "--- Step 0: Checking System Dependencies ---"
if [[ "$(uname)" == "Darwin" ]]; then
    install_macos_deps
elif command_exists apt-get; then
    install_debian_deps
elif command_exists dnf || command_exists yum; then
    install_fedora_deps
else
    echo "Warning: Could not determine OS/package manager."
    echo "Please ensure you have a C compiler (gcc/clang) and Python build dependencies installed."
    echo "(e.g., openssl, zlib, readline, sqlite3, xz/lzma, bzip2)"
    sleep 5
fi

# Step 1: Check or install pyenv
# =========================================================
echo -e "\n--- Step 1: Setting up pyenv ---"
if [ ! -d "$HOME/.pyenv" ]; then
  echo "pyenv installation not found. Installing pyenv..."
  # Use a non-interactive install
  curl https://pyenv.run | bash
fi

# Add pyenv to PATH and initialize it for the current session
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"


# Step 2: Install Python 3.10.14 if not already installed
# =========================================================
echo -e "\n--- Step 2: Installing Python ---"
PYTHON_VERSION="3.10.14" # Define version for easy updates
if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
  echo "Installing Python ${PYTHON_VERSION} via pyenv... (This may take several minutes)"
  # Set environment variables for pyenv to find Homebrew-installed libraries on macOS
  if [[ "$(uname)" == "Darwin" ]]; then
      echo "Configuring build environment for macOS..."
      export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/lib -L$(brew --prefix xz)/lib"
      export CPPFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix readline)/include -I$(brew --prefix zlib)/include -I$(brew --prefix bzip2)/include -I$(brew --prefix xz)/include"
  fi
pyenv install "${PYTHON_VERSION}"
else
    echo "Python ${PYTHON_VERSION} is already installed."
fi


# Step 3: Set Python version for pipx
# =========================================================
echo -e "\n--- Step 3: Configuring pipx ---"
# Point pipx to the specific pyenv-managed Python executable
export PIPX_DEFAULT_PYTHON="$(pyenv root)/versions/${PYTHON_VERSION}/bin/python"

echo "pipx will use Python at: $PIPX_DEFAULT_PYTHON"

# Step 4: Use pipx to install
# =========================================================
echo -e "\n--- Step 4: Installing ARIBrain ---"
pipx install --python "$PIPX_DEFAULT_PYTHON" git+https://github.com/AriBrain/ari-core.git

echo ""
echo "✅ ARIBrain installation complete!"
echo "To run the application, open a new terminal and type: aribrain"




# #!/bin/bash
# set -e # Exit immediately if a command exits with a non-zero status.

# # Step 0: Check for and install compiler tools if missing
# # =========================================================
# if ! command -v gcc &> /dev/null; then
#     echo "C/C++ compiler not found. An attempt will be made to install the required tools."

#     # Check for macOS
#     if [[ "$(uname)" == "Darwin" ]]; then
#         echo "On macOS, Xcode Command Line Tools are required."
#         echo "This script will now attempt to launch the installer."
#         echo "Please follow the on-screen GUI prompts to complete the installation."
        
#         # This command launches the GUI installer. The script cannot wait for it to finish.
#         xcode-select --install
        
#         echo ""
#         echo "IMPORTANT: After the Xcode Command Line Tools installation is complete, please re-run this script to continue installing ARIBrain."
#         exit 1 # Exit the script, requiring the user to run it again after the tools are installed.

#     # Check for Debian/Ubuntu (uses apt)
#     elif command -v apt-get &> /dev/null; then
#         echo "On Debian/Ubuntu, the 'build-essential' package is required."
#         read -p "Install 'build-essential' using sudo apt? (y/n) " -n 1 -r
#         echo
#         if [[ $REPLY =~ ^[Yy]$ ]]; then
#             echo "Running 'sudo apt update && sudo apt install -y build-essential'..."
#             sudo apt update
#             sudo apt install -y build-essential
#         else
#             echo "Compiler installation skipped. Please install 'build-essential' manually and re-run this script."
#             exit 1
#         fi

#     # Check for Fedora/CentOS/RHEL (uses dnf/yum)
#     elif command -v dnf &> /dev/null || command -v yum &> /dev/null; then
#         echo "On Fedora/CentOS/RHEL, 'Development Tools' are required."
#         read -p "Install 'Development Tools' using sudo? (y/n) " -n 1 -r
#         echo
#         if [[ $REPLY =~ ^[Yy]$ ]]; then
#             if command -v dnf &> /dev/null; then
#                 echo "Running 'sudo dnf groupinstall -y \"Development Tools\"'..."
#                 sudo dnf groupinstall -y "Development Tools"
#             else
#                 echo "Running 'sudo yum groupinstall -y \"Development Tools\"'..."
#                 sudo yum groupinstall -y "Development Tools"
#             fi
#         else
#             echo "Compiler installation skipped. Please install 'Development Tools' manually and re-run this script."
#             exit 1
#         fi
#     else
#         echo "Could not determine Linux distribution or package manager."
#         echo "Please install the equivalent of 'build-essential' or 'Development Tools' for your system and re-run this script."
#         exit 1
#     fi
# else
#     echo "Compiler (gcc) found."
# fi


# # Step 1: Check or install pyenv
# # =========================================================
# if ! command -v pyenv &> /dev/null; then
#   echo "Installing pyenv..."
#   # Use a non-interactive install if possible
#   curl https://pyenv.run | bash
# fi

# # Add pyenv to PATH and initialize it for the current session
# export PATH="$HOME/.pyenv/bin:$PATH"
# eval "$(pyenv init --path)"
# eval "$(pyenv init -)"


# # Step 2: Install Python 3.10.14 if not already installed
# # =========================================================
# PYTHON_VERSION="3.10.14" # Define version for easy updates
# if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
#   echo "Installing Python ${PYTHON_VERSION} via pyenv... (This may take several minutes)"
#   pyenv install "${PYTHON_VERSION}"
# fi


# # Step 3: Set Python version for pipx
# # =========================================================
# # Point pipx to the specific pyenv-managed Python executable
# export PIPX_DEFAULT_PYTHON="$(pyenv root)/versions/${PYTHON_VERSION}/bin/python"


# # Step 4: Use pipx to install
# # =========================================================
# echo "Installing ARIBrain using pipx with Python ${PYTHON_VERSION}..."
# pipx install --python "$PIPX_DEFAULT_PYTHON" git+https://github.com/AriBrain/ari-core.git

# echo ""
# echo "✅ ARIBrain installation complete!"
# echo "To run the application, type: aribrain"



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
