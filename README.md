# ARI Brain

## Overview  
ARIbrain: All-Resolutions Inference for fMRI

ARIbrain is an advanced neuroimaging application designed to enhance the spatial specificity and interpretability of functional MRI (fMRI) analyses. It implements the All-Resolutions Inference (ARI) framework, a statistical method that quantifies the proportion of truly active voxels within any selected cluster, thereby addressing the limitations of traditional cluster-based inference methods.

### What It Does
- **True Discovery Proportion (TDP) Estimation**: Calculates lower bounds for the proportion of active voxels within clusters, providing a more nuanced understanding of brain activation patterns.  
- **Multi-Resolution Analysis**: Enables inference at various spatial scales, from large clusters to individual voxels, facilitating detailed exploration of neural activity.  
- **Integration with Standard fMRI Tools**: Compatible with outputs from popular fMRI analysis packages (e.g., SPM, FSL, AFNI), allowing seamless incorporation into existing workflows.

### Key Features
- **Interactive Visualization**: Offers intuitive visualization of activation maps and TDP estimates, aiding in the interpretation of complex data.  
- **Template Alignment**: Aligns statistical maps to standard brain templates, ensuring consistency across studies and subjects.  
- **Efficient Computation**: Utilizes optimized algorithms for rapid processing of large neuroimaging datasets.

### Why It’s Useful  
Traditional cluster-wise inference methods in fMRI often suffer from the “spatial specificity paradox,” where larger clusters may be statistically significant but contain a low proportion of truly active voxels. ARIbrain addresses this issue by providing a rigorous statistical framework to estimate the TDP within clusters, enhancing the reliability and interpretability of neuroimaging results.

---
---

## Installation

### ARIBrain Installation Guide

This guide provides platform-specific instructions for installing ARIBrain desktop application using pipx. The installer automatically sets up Python 3.10.X, creates a virtual environment, and compiles C++ extensions. Works on macOS and Linux.

---

### macOS & Linux
The installation script automates the setup of Python, dependencies, and C++ extensions.


### Prerequisites

- A C compiler (e.g., Xcode Command Line Tools on macOS, or `build-essential` on Debian/Ubuntu).
- `curl` to download the installer.
- Python 3.10.X (will be installed automatically via pyenv if missing)
- pipx (used to isolate app installs in their own environment)

### 1. Install pipx

If you don’t already have pipx, install it like this:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Then restart your shell (close and reopen Terminal, or run `exec "$SHELL"`).

### 2. Install ARIBrain (One-liner)

Run the following in your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/AriBrain/ari-core/main/install.sh | bash
```

This will:

- Install pyenv to manage Python versions (if missing)
- Install Python 3.10.14 (if missing)
- Create a dedicated environment (`aribrain`) in: ` ~/.local/pipx/venvs/aribrain`
- Use pipx to install ARIBrain from GitHub

### 3. Run ARIBrain

After installation, simply run:

```bash
aribrain
```

This launches the application GUI.

---

### Optional: Reinstall or Clean Up

If something goes wrong or you want to reset the installation:

```bash
pipx uninstall aribrain
rm -rf ~/.local/pipx/venvs/aribrain
rm -rf ~/.local/bin/aribrain
rm -rf ~/.pyenv/versions/3.10.14
```

### Virtual Environment Location

The app will be installed in:

```
~/.local/pipx/venvs/aribrain
```

The virtualenv uses Python 3.10.14 provided by pyenv, isolated from your system Python.

### Notes

- The application is fetched from the GitHub repo: https://github.com/AriBrain/ari-core
- Make sure your system has a compiler installed (e.g., Xcode Command Line Tools on macOS).

---

## Windows Installation

This installation method uses a PowerShell script to automate the setup on Windows 10 and 11.

### 1. Install Prerequisites (One-time Setup)

Before running the main installer, a few tools are needed. The following steps will guide you through setting them up using PowerShell.

#### Install Python (if not already on your system)

- Go to https://www.python.org/downloads/windows to download and run the installer.
- **Important**: Check the box for **"Add python.exe to PATH"** during installation.

#### Install Git

Open PowerShell and run the following command:

```powershell
winget install --id Git.Git -e --source winget
```

#### Install pipx

Open a new PowerShell terminal, then run:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

Close and reopen the PowerShell terminal after this step.

---

### 2. Install ARIBrain (One-liner)

Run the following command in a fresh PowerShell terminal:

```powershell
powershell -NoExit -Command "& {Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; iwr -useb https://raw.githubusercontent.com/AriBrain/ari-core/main/install.ps1 | iex}"
```

This script will:

- Install the Microsoft C++ Build Tools if missing (this may take time)
- Install `pyenv-win` if missing
- Use `pyenv-win` to install Python 3.10.11 if needed
- Use `pipx` to install ARIBrain from GitHub in an isolated environment

---

### 3. Troubleshooting

If you get an error about **Microsoft Visual C++ 14.0 or greater**, the build tools likely didn't install correctly.

To fix this manually:

1. Open **Start Menu** and run **Visual Studio Installer**
2. Find **Visual Studio Build Tools 2022** and click **Modify**
3. In the **Workloads** tab, check **Desktop development with C++**
4. Click **Modify** to install
5. Re-run the installation command from Step 2

---

## Running ARIBrain (All Platforms)

After installation, launch the application by running:

```bash
aribrain
```

This will open the application GUI.

---

## Reinstalling or Cleaning Up

To uninstall ARIBrain:

```bash
pipx uninstall aribrain
Remove-Item -Path "$env:USERPROFILE\.local\pipx\venvs\aribrain" -Recurse -Force
Remove-Item -Path "$env:USERPROFILE\.local\bin\aribrain" -Recurse -Force
Remove-Item -Path "$env:USERPROFILE\.pyenv\pyenv-win\versions\3.10.11" -Recurse -Force

---
---

## Contributing to ARIBrain (Internal Team)

This repository is actively maintained by the ARIBrain development team. If you are a contributor with internal access, please follow the workflow below to ensure smooth collaboration.

---

### Workflow Overview

1. **Fork the Repository**
   - Navigate to: https://github.com/AriBrain/ari-core
   - Click on **Fork** (top-right corner).
   - This will create a copy under your personal GitHub account.

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ari-core.git
   cd ari-core
   ```

3. **Add Upstream Remote**
   This lets you pull updates from the official repo.
   ```bash
   git remote add upstream https://github.com/AriBrain/ari-core.git
   ```

4. **Create a New Feature or Fix Branch**
   Always branch off from `main`:
   ```bash
   git checkout main
   git fetch upstream
   git merge upstream/main
   git checkout -b feat/your-feature-name
   ```

5. **Develop and Commit**
   - Write your code and commit changes with meaningful messages.
   - Follow existing coding and style conventions.

6. **Push Your Branch**
   ```bash
   git push origin feat/your-feature-name
   ```

7. **Create a Pull Request (PR)**
   - Go to your fork on GitHub.
   - Open a PR against `AriBrain/ari-core:main`.
   - Add a short description and context for your changes.

8. **Review and Merge**
   - One team member reviews and approves your PR.
   - You or the reviewer merges once approved.

---

### Development Guidelines

- Use Python **3.10.14**
- All C++ extensions must compile cleanly across platforms (macOS, Linux)
- Install dependencies via `requirements.txt` or `pyproject.toml`
- Use `pipx` and `pyenv` for isolated testing

---

### Staying Updated

To keep your local fork up to date:
```bash
git fetch upstream
git checkout main
git merge upstream/main
```