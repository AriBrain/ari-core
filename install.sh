#!/bin/bash

# Step 1: Check or install pyenv
if ! command -v pyenv &> /dev/null; then
  echo "Installing pyenv..."
  curl https://pyenv.run | bash
  export PATH="$HOME/.pyenv/bin:$PATH"
  eval "$(pyenv init --path)"
  eval "$(pyenv init -)"
fi

# Step 2: Install Python 3.10.14 if not already installed
if ! pyenv versions --bare | grep -q "3.10.14"; then
  echo "Installing Python 3.10.14 via pyenv..."
  pyenv install 3.10.14
fi

# Step 3: Use pyenv to create a virtual environment
export PIPX_DEFAULT_PYTHON="$(pyenv root)/versions/3.10.14/bin/python3.10"

# Step 4: Use pipx to install
echo "Installing ARIBrain using pipx with Python 3.10.14..."
#pipx install --python "$PIPX_DEFAULT_PYTHON" git+https://github.com/AriBrain/ari-core.git
pipx install --python --force "$PIPX_DEFAULT_PYTHON" 'git+https://github.com/wdweeda/ari-core.git@feat/tmapfix'

## !/bin/bash

# set -e  # Exit on error

# # Step 1: Ensure pyenv is installed
# if ! command -v pyenv &> /dev/null; then
#   echo "Installing pyenv..."
#   curl https://pyenv.run | bash
#   export PATH="$HOME/.pyenv/bin:$PATH"
#   eval "$(pyenv init --path)"
#   eval "$(pyenv init -)"
# fi

# # Step 2: Ensure Python 3.10.14 is installed
# if ! pyenv versions --bare | grep -q "3.10.14"; then
#   echo "Installing Python 3.10.14 via pyenv..."
#   pyenv install 3.10.14
# fi

# # Step 3: Create virtual environment in ~/aribrain_venv
# VENV_PATH="$HOME/aribrain_venv"
# PYTHON_BIN="$(pyenv root)/versions/3.10.14/bin/python3.10"

# if [ ! -d "$VENV_PATH" ]; then
#   echo "Creating virtual environment at $VENV_PATH..."
#   "$PYTHON_BIN" -m venv "$VENV_PATH"
# fi

# # Step 4: Activate venv and install your app
# echo "Activating virtual environment and installing ARIBrain..."
# source "$VENV_PATH/bin/activate"

# pip install --upgrade pip setuptools wheel
# pip install git+https://github.com/AriBrain/ari-core.git

# # Step 5: Create a run alias (optional)
# echo "Creating launch script ~/aribrain..."
# echo "#!/bin/bash
# source \"$VENV_PATH/bin/activate\"
# aribrain \"\$@\"" > "$HOME/aribrain"
# chmod +x "$HOME/aribrain"

# echo "✅ ARIBrain installed.
# To run the app: ~/aribrain"