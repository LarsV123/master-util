#!/bin/bash

# Script for building MySQL

# Exit on error
set -e

# Exit if an undefined variable is used
set -u

# Exit if a command in a pipeline fails
set -o pipefail

# Print commands before executing them (useful for debugging)
# set -x

# The script assumes that the project is placed at ~/mysql,
# with the mysql-server folder at ~/mysql/mysql-server

# Create a directory for boost if it does not exist
BOOST_FOLDER=~/mysql/boost
mkdir -p $BOOST_FOLDER
if [ ! -d $BOOST_FOLDER ]; then
  echo "Error: ~/mysql/boost does not exist."
  exit 1
fi

DATA_DIR=~/mysql/mysql-data
# Create the data directory if it does not exist
mkdir -p $DATA_DIR
if [ ! -d $DATA_DIR ]; then
  echo "Error: $DATA_DIR does not exist."
  exit 1
fi

# Default values for optional command-line arguments
DEBUG_BUILD=false
NINJA_THREADS=4 # More threads require more RAM (> 16 GB)

# Parse command-line arguments
while getopts "b:t:d" opt; do
  case $opt in
  b)
    BUILD_DIR="$OPTARG"
    ;;
  t)
    NINJA_THREADS="$OPTARG"
    ;;
  d)
    DEBUG_BUILD=true
    ;;
  ?)
    echo "Invalid option: -$OPTARG" >&2
    exit 1
    ;;
  :)
    echo "Option -$OPTARG requires an argument." >&2
    exit 1
    ;;
  esac
done

if [ -z $BUILD_DIR ]; then
  echo "Error: BUILD_DIR must be specified with -b option."
  exit 1
fi

# Create build folder (no error if it already exists)
mkdir -p $BUILD_DIR
if [ ! -d $BUILD_DIR ]; then
  echo "Error: $BUILD_DIR does not exist."
  exit 1
fi

cd $BUILD_DIR
echo "Building MySQL in folder: $PWD"

echo "Running cmake"

if [ $DEBUG_BUILD = true ]; then
  echo "Building in debug mode"
  CMAKE_BUILD_TYPE="-DWITH_DEBUG=1 \
                    -DWITH_ASAN=1 \
                    -DMYSQL_MAINTAINER_MODE=1 \
                    -DCMAKE_BUILD_TYPE=Debug"
else
  echo "Building in release mode"
  CMAKE_BUILD_TYPE="-DWITH_DEBUG=0 \
                    -DWITH_ASAN=0"
fi

CMAKE_ARGS=(
  "../mysql-server/"
  "$CMAKE_BUILD_TYPE"
  "-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON"
  "-DWITH_SYSTEM_LIBS=0"
  "-DWITH_UNIT_TESTS=0"
  "-DWITH_ROUTER=0"
  "-DWITH_AUTHENTICATION_FIDO=0"
  "-DWITH_NDB=0"
  "-DWITH_ZLIB=bundled"
  "-DDOWNLOAD_BOOST=1"
  "-DWITH_BOOST=~/mysql/boost"
  "-DWITH_NDBCLUSTER_STORAGE_ENGINE=0"
  "-DWITH_ICU=system"
  "-GNinja"
)

# Run cmake and exit if it fails
if ! cmake "${CMAKE_ARGS[@]}"; then
  echo "Error: cmake failed."
  exit 1
fi

if ! echo "$NINJA_THREADS" | grep -qE '^[0-9]+$'; then
  echo "Error: NINJA_THREADS must be a valid integer."
  exit 1
fi

# Run ninja and exit if it fails
if ! ninja -j$NINJA_THREADS; then
  echo "Error: ninja failed."
  exit 1
fi

echo "Done building MySQL"

PATH="~/mysql/${BUILD_DIR}/runtime_output_directory"
SERVER_OPTIONS="--datadir=${DATA_DIR} --port=3306 --sort_buffer_size=2048M --innodb_buffer_pool_size=2048M"
INIT_SERVER="${PATH}/mysqld ${SERVER_OPTIONS} --initialize-insecure"
RUN_SERVER="${PATH}/mysqld ${SERVER_OPTIONS}"
RUN_CLIENT="${PATH}/mysql -uroot"

printf "\n**********\n"
printf "Initialize server:\n  ${INIT_SERVER}\n"
printf "Run server:\n  ${RUN_SERVER}\n"
printf "Run client:\n  ${RUN_CLIENT}\n"

exit 0
