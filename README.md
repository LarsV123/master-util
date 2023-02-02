# Setup

Prerequisites:

- Python 3.9 or greater

```bash
# Run setup script to install dependencies and test CLI
bash scripts/setup.sh
```

# Development

Run these commands to check formatting, linting and types before committing:

```bash
black . && flake8 . && mypy .
```

These should not produce any errors.

It is recommended to create a git precommit hook to run these commands before pushing changes to the repository. To do this, copy the file `scripts/pre-push` to `.git/hooks/pre-push`.

# Usage

```bash
# Alias the start script for convenience
alias cli="python src/cli.py"
```
