#!/bin/bash
# Run this file to set up the project

# This is used to abort the script if any command fails
set -e

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Running test to verify database connection can be made..."
python src/cli.py -v test

echo "Initializing migrations table..."
python src/migrate.py init

echo "Setup script completed successfully."
