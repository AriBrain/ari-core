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
pipx install --python "$PIPX_DEFAULT_PYTHON" git+https://github.com/AriBrain/ari-core.git