# My Application

## Overview
ARIbrain: All-Resolutions Inference for fMRI

ARIbrain is an advanced neuroimaging application designed to enhance the spatial specificity and interpretability of functional MRI (fMRI) analyses. It implements the All-Resolutions Inference (ARI) framework, a statistical method that quantifies the proportion of truly active voxels within any selected cluster, thereby addressing the limitations of traditional cluster-based inference methods. ￼ ￼

What It Does
	•	True Discovery Proportion (TDP) Estimation: Calculates lower bounds for the proportion of active voxels within clusters, providing a more nuanced understanding of brain activation patterns. ￼
	•	Multi-Resolution Analysis: Enables inference at various spatial scales, from large clusters to individual voxels, facilitating detailed exploration of neural activity.
	•	Integration with Standard fMRI Tools: Compatible with outputs from popular fMRI analysis packages (e.g., SPM, FSL, AFNI), allowing seamless incorporation into existing workflows. ￼

Key Features
	•	Interactive Visualization: Offers intuitive visualization of activation maps and TDP estimates, aiding in the interpretation of complex data.
	•	Template Alignment: Aligns statistical maps to standard brain templates, ensuring consistency across studies and subjects.
	•	Efficient Computation: Utilizes optimized algorithms for rapid processing of large neuroimaging datasets.

Why It’s Useful

Traditional cluster-wise inference methods in fMRI often suffer from the “spatial specificity paradox,” where larger clusters may be statistically significant but contain a low proportion of truly active voxels. ARIbrain addresses this issue by providing a rigorous statistical framework to estimate the TDP within clusters, enhancing the reliability and interpretability of neuroimaging results.


## Installation

ARIBrain Installation Guide

This document outlines how to install and run the ARIBrain desktop application using pipx. The installer automatically sets up Python 3.10.14, creates a virtual environment, and compiles C++ extensions. Works on macOS and Linux.
 
Prerequisites
•	Python 3.10.14 (will be installed automatically via pyenv if missing)
•	pipx (used to isolate app installs in their own environment)
 
1. Install 
pipx

If you don’t already have pipx, install it like this:
python3 -m pip install --user pipx
python3 -m pipx ensurepath
Then restart your shell (close and reopen Terminal, or run exec "$SHELL").
 
2. Install ARIBrain (One-liner)

Run the following in your terminal:
curl -sSL https://raw.githubusercontent.com/AriBrain/ari-core/main/install.sh | bash
This will:
•	Install pyenv (if missing)
•	Install Python 3.10.14 (if missing)
•	Create a dedicated environment named aribrain_venv
•	Use pipx to install ARIBrain from GitHub
 
3. Run ARIBrain

After installation, simply run:
aribrain
This launches the application GUI.
 
Optional: Reinstall or Clean Up

If something goes wrong or you want to reset the installation:
pipx uninstall aribrain
rm -rf ~/.local/pipx/venvs/aribrain
rm -rf ~/.local/bin/aribrain
rm -rf ~/.pyenv/versions/3.10.14
 
📁 Virtual Environment Location

The app will be installed in:
~/.local/pipx/venvs/aribrain
The virtualenv uses Python 3.10.14 provided by pyenv, isolated from your system Python.
 
Notes
•	The application is fetched from the GitHub repo: https://github.com/AriBrain/ari-core
•	Make sure your system has a compiler installed (e.g., Xcode Command Line Tools on macOS).

### Prerequisites
- will be installed automatically into the venv created by pipx

