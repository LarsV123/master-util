# README

This repository contains various utilities for my master's thesis project.
They are used for benchmarking and testing a MySQL server.
As the project requires building and running a MySQL server from source code,
instructions to do so are also included.

The instructions below are intended for my own personal use, and some steps are
optional or may need to be adapted somewhat to fit other uses.
For example, the instructions were developed while working on a Windows machine running Ubuntu 20.04 in WSL2 and later reworked to work on a Linux machine running Ubuntu 22 natively.

Note that the instructions and various scripts assume that the project is placed
in the root of the user's home directory as a directory named `mysql`.

# Prerequisites

This section covers prerequisites needed to build the project.

```bash
# Update package manager
sudo apt update

# Clone this repository
git clone https://github.com/LarsV123/master-util.git ~/mysql
cd ~/mysql

# Download source data used for testing
git clone https://github.com/umpirsky/country-list.git data/country-list

# Download FlameGraph util for generating flame graphs
git clone https://github.com/brendangregg/FlameGraph flamegraph

# Create an .env file with username, password and host for the MySQL server
cp .env-template .env # Copy the template
vim .env # Edit the template and set the environment variables
```

# MySQL

This section covers cloning, building and running a MySQL server.

## Setup

```bash
# Clone my fork of MySQL and switch to the development branch
git clone https://github.com/LarsV123/mysql-server.git
cd mysql-server
git checkout create-custom-collation

# Install all dependencies needed to build MySQL
## Build tools
sudo apt install make ninja-build g++ clang bison cmake pkg-config

## Debuggers and test tools
sudo apt install lld lldb ddd xterm libjson-perl doxygen plantuml dia \
libcanberra-gtk-module clang-tidy

## Other dependencies
sudo apt install libssl-dev libncurses-dev libldap-dev libsasl2-dev \
libudev-dev libzstd-dev libedit-dev liblz4-dev libcurl4-openssl-dev \
protobuf-compiler dpkg-dev
```

## Usage

```bash
# Build MySQL (takes a while on the first run). Do this for every code change.
bash build.sh -b <build-directory>

# FIRST TIME ONLY: Initialize MySQL data directory
~/mysql/<build-directory>/runtime_output_directory/mysqld --datadir=../mysql-data --initialize-insecure

# Run MySQL server
~/mysql/<build-directory>/runtime_output_directory/mysqld --datadir=../mysql-data

# Start client (from separate terminal)
~/mysql/<build-directory>/runtime_output_directory/mysql -uroot

# FIRST TIME ONLY: With the client, create the database and user in .env
CREATE DATABASE <database>;
CREATE USER '<user>'@'%<host>' IDENTIFIED BY '<password>';
GRANT ALL PRIVILEGES ON *.* TO '<user>'@'%<host>';
```

# Python utils

This section covers building and configuring the Python utilities,
which are used for running the experiments.

## pyenv

Using `pyenv` is optional, but highly recommended. It allows you to easily
switch between different Python versions and virtual environments.

```bash
# Install required dependencies
sudo apt update
sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl liblzma-dev \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev

# Install pyenv
cd ~
curl https://pyenv.run | bash

# Set shell variables
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile
source ~/.bashrc

# If you use WSL, you may need to do the following:
## Disable Windows additions to PATH (if needed)
sudo vim /etc/wsl.conf

## Add this and save the file:
[interop]
appendWindowsPath = false

## Exit and restart WSL, then check that $PATH no longer shows Windows paths
echo $PATH

# Set up a Python virtual environment with pyenv
pyenv install 3.11.2
pyenv virtualenv 3.11.2 3.11.2-master-util
pyenv local 3.11.2-master-util
pyenv shell 3.11.2-master-util
```

## Setup

```bash
# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Check that a MySQL server is running and that we have access to it
python src/cli.py -v test
```

## Development

```bash
# Check formatting, linting and types (should not produce any errors)
black src --check && flake8 src && mypy src

# Fix formatting automatically
black src

# Update the requirements files if dependencies have changed
pip-compile requirements.in --resolver=backtracking
pip install -r requirements.txt
```

## Running experiments

This section covers running the experiments included in the thesis.
These include performance benchmarks, validation tests and profiling.

### Setup

```bash
# Optional: Create alias for the CLI tool
echo 'alias cli="python ~/mysql/src/cli.py"' >> ~/.bashrc
source ~/.bashrc

# Test the CLI
cli --help
cli -v test

# Insert test data
cli init
```

### Performance benchmarks

```bash
# See available options
cli perf --help
```

### Flame graphs & perf

To generate flame graphs, we use the utilities `perf` and `FlameGraph`.

Source:
https://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html

The basic concept is that we start recording activity in the MySQL server process with `perf` from one terminal, and then start a Python script in a separate terminal which executes a "stresstest" query. After the recording is done, we can generate a flame graph from the recorded data.

Example usage of `perf` and `FlameGraph` without the bash script:

```bash
cd FlameGraph

# Find PID of mysqld process
ps aux | grep mysqld
-> 14147

# Start perf recording in one terminal
perf record -p 14147 -F 4000 -g -- sleep 30
# -p 14147: record activity in process with PID 14147
# -g: record call graph
# -F 4000: sample frequency
# -- sleep 30: record for 30 seconds

# Test ICU collation using Python script in another terminal
python src/cli.py stresstest -c utf8mb4_icu_en_US_ai_ci # or: utf8mb4_0900_ai_ci

# Create flame graph
perf script | ./stackcollapse-perf.pl > out.perf-folded
./flamegraph.pl out.perf-folded > utf8mb4_icu_en_US_ai_ci.svg # or: utf8mb4_0900_ai_ci.svg
```

The flamegraphs in the report were generated using a bash script, which is included.

```bash
# Build MySQL server with ICU_frozen config
# This means setting these values in mysql-server/strings/ctype-icu.h
# ICU_FROZEN=true
# ICU_EXTRA_TAILORING=false
bash build.sh -b "build-frozen"

# Start it
~/mysql/build-frozen/runtime_output_directory/mysqld --datadir=<user_directory>/mysql/mysql-data --sort_buffer_size=2048M --innodb_buffer_pool_size=2048M

# Start client (from separate terminal)
~/mysql/build-frozen/runtime_output_directory/mysql -uroot

# Find PID of mysqld process
ps aux | grep mysqld

# Run series of tests to generate flamegraphs as .svg files
bash experiment2.sh -p <pid>
```

### Validation tests

The validation tests are intended to check that two collations produce identical
results. This is done by compiling two versions of the MySQL server, one with
the original collation and one with the new collation, and then running a set
of queries on both servers and comparing the results.

Example usages of the test:

```bash
# Compare the ICU and MySQL versions of the same collation (will fail, as they differ):
cli validate -p1 3306 -p2 3306 -c1 "utf8mb4_icu_nb_NO_ai_ci" -c2 "utf8mb4_nb_0900_ai_ci"

# Compare the same ICU collation on different builds of MySQL:
cli validate -p1 3306 -p2 3307 -c1 "utf8mb4_icu_nb_NO_ai_ci" -c2 "utf8mb4_icu_nb_NO_ai_ci"
```

The two MySQL servers need to be running with separate ports, socket files and data directories.
Instructions for running all the validation tests, i.e. "experiment 3":

```bash
# Run servers
~/mysql/build-frozen/runtime_output_directory/mysqld \
--datadir=/home/lv123/mysql/mysql-data \
--port=3306 \
--mysqlx-port=33061 \
--mysqlx-socket=/tmp/mysqlx1.sock \
--socket=/tmp/mysql1.sock


~/mysql/build-locale/runtime_output_directory/mysqld \
--datadir=/home/lv123/mysql/mysql-data-alt \
--port=3307 \
--mysqlx-port=33062 \
--mysqlx-socket=/tmp/mysqlx2.sock \
--socket=/tmp/mysql2.sock

# Run clients
~/mysql/build-frozen/runtime_output_directory/mysql -uroot -P3306 \
--socket=/tmp/mysql1.sock

~/mysql/build-locale/runtime_output_directory/mysql -uroot -P3307 \
--socket=/tmp/mysql2.sock

# Run the experiments
bash ~/mysql/src/experiment3.sh
```
