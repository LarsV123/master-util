# Setup

Prerequisites:

- Python 3.9 or greater

```bash
# Run setup script to install dependencies and test CLI
bash scripts/setup.sh

# Initialize migrations table
python src/migrate.py init

# Download source data used for testing
git clone git@github.com:umpirsky/country-list.git data/country-list
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
# Create aliases for the CLI tools for convenience
alias cli="python src/cli.py"
alias migrate="python src/migrate.py"

# Test the CLI
cli --help
cli -v test

# Run migrations
migrate --help
migrate make
migrate up
```
