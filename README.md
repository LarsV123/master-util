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

# FlameGraph util for generating flame graphs
git clone https://github.com/brendangregg/FlameGraph flamegraph
```

## MySQL

This project is intended to be used with a MySQL database server.

Run MySQL server:

```bash
./runtime_output_directory/mysqld --datadir=../data

# Install MySQL client (this is for Ubuntu, but it should be similar for other distros)
sudo apt install mysql-shell
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

# Insert test data
cli init

# Set up and run a quick test
cli setup1
cli test1
```

## Flame graphs & perf

To generate flame graphs, we use the utilities `perf` and `FlameGraph`.

Source:
https://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html

```bash
wsl

# Find PID of mysqld process
ps aux | grep mysqld

# Generate flame graph
cd FlameGraph
perf record -p <pid> -F 99 -a -g -- sleep 60
perf record -F 99 -g -p 3657 -- sleep 10
perf script | ./stackcollapse-perf.pl > out.perf-folded
./flamegraph.pl out.perf-folded > perf.svg
```
