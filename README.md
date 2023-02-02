# Setup

Prerequisites:

- Python 3.9 or greater

```bash
# Run setup script to install dependencies and test CLI
bash setup.sh
```

# Development

Run these commands to check formatting, linting and types before committing:

```bash
black . && flake8 . && mypy .
```

These should not produce any errors.

# Usage

```bash
# Alias the start script for convenience
alias cli="python src/cli.py"
```
