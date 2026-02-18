# SMLM ROI Selector - Binder Ready

This repository is configured to run on **Binder**, allowing you to try the application directly in your web browser without local installation.

## Launch on Binder

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ngimber/SMLM_ROI-Selector/main)

Click the badge above to launch an interactive Binder environment where you can run:
```bash
python smlm_roi_selector.py
```

## Binder Configuration Files

This repository includes the following files for Binder compatibility:

- **`environment.yml`** - Conda environment specification with all dependencies
- **`postBuild`** - Build script that runs after environment setup
- **`requirements.txt`** - Python package dependencies

## How to Use

1. Click the Binder badge above
2. Wait for the environment to build and launch
3. Open a terminal in Binder
4. Run: `python smlm_roi_selector.py`

## Local Usage

For local installation, see the main [README](README.md) for standard installation instructions.

## Notes

- The GUI runs in the Binder terminal environment
- For persistent work, download your processed ROI files before the session ends
- Sessions have a time limit (typically 10 minutes of inactivity)

---

**Original Project:** [SMLM ROI Selector](https://github.com/ngimber/SMLM_ROI-Selector)
