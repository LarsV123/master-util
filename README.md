# README

This repository contains client-side utilities for my master's thesis project.
They are used for benchmarking and testing a MySQL server.

# Setup

## Prerequisites

- Set up `pyenv`
- Compile MySQL from source (see separate repository)
- Copy `.env.example` to `.env` and set the environment variables

```bash
# Download source data used for testing
git clone git@github.com:umpirsky/country-list.git data/country-list

# Download FlameGraph util for generating flame graphs
git clone https://github.com/brendangregg/FlameGraph flamegraph
```

## MySQL

```bash
# Run MySQL server
~/mysql/release-build/runtime_output_directory/mysqld --datadir=../data

# Start client (from separate terminal) for initial setup
~/mysql/release-build/runtime_output_directory/mysql -uroot

# With the client, create the user specified in .env
CREATE USER '<user>'@'%<host>' IDENTIFIED BY '<password>';
GRANT ALL PRIVILEGES ON *.* TO '<user>'@'%<host>';
```

## Python

```bash
# Set up a Python virtual environment with pyenv (recommended method)
pyenv install 3.11.2
pyenv virtualenv 3.11.2 3.11.2-master-util
pyenv local 3.11.2-master-util
pyenv shell 3.11.2-master-util

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Check that a MySQL server is running and that we have access to it
python src/cli.py -v test

# Initialize migrations table
python src/migrate.py init
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

The basic concept is that we start recording activity in the MySQL server process with `perf` from one terminal, and then start a Python script in a separate terminal which executes a "stresstest" query. After the recording is done, we can generate a flame graph from the recorded data.

Example usage:

```bash
cd FlameGraph

# Find PID of mysqld process
ps aux | grep mysqld
-> 14147

# Start perf recording in one terminal
perf record -p 14147 -F 4000 -g -- sleep 30

# Test ICU collation using Python script in another terminal
python src/cli.py stresstest -c utf8mb4_icu_en_US_ai_ci # or: utf8mb4_0900_ai_ci

# Create flame graph
perf script | ./stackcollapse-perf.pl > out.perf-folded
./flamegraph.pl out.perf-folded > utf8mb4_icu_en_US_ai_ci.svg # or: utf8mb4_0900_ai_ci.svg
```
