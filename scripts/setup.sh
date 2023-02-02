#!/bin/bash
# Run once to set up the project

# This is used to abort the script if any command fails
set -e

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Creating alias 'cli' for 'python src/cli.py'..."
alias cli="python src/cli.py"

echo "Running test to verify database connection can be made..."
python src/cli.py -v test

echo "Setup script completed successfully."
