#!/usr/bin/env bash
# Activate argcomplete globally for all PYTHON_ARGCOMPLETE_OK scripts.
# Run once per shell session, or add to ~/.bashrc / ~/.zshrc:
#   source ~/LanguagePodcast/backend/scripts/activate_autocomplete.sh

# Use the Python 3 variant (required on Ubuntu/Debian)
if command -v activate-global-python-argcomplete3 &>/dev/null; then
    activate-global-python-argcomplete3
elif command -v activate-global-python-argcomplete &>/dev/null; then
    activate-global-python-argcomplete
else
    echo "argcomplete not found. Run: pip install argcomplete"
fi
