#!/bin/bash

# Script for building MySQL

# The script assumes that the project is placed at ~/mysql,
# with the mysql-server folder at ~/mysql/mysql-server
DATA_DIR=~/mysql/mysql-data

# Exit on error
set -e

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

if [ -z "$BUILD_DIR" ]; then
  echo "Error: BUILD_DIR must be specified with -b option."
  exit 1
fi

if [ -z "$NINJA_THREADS" ]; then
  NINJA_THREADS=4
fi

# Create build folder (no error if it already exists)
mkdir -p $BUILD_DIR
cd $BUILD_DIR
echo "Building MySQL in folder: $PWD"

echo "Running cmake"

if [ "$DEBUG_BUILD" = true ]; then
  CMAKE_BUILD_TYPE="-DWITH_DEBUG=1 \
                    -DWITH_ASAN=1 \
                    -DMYSQL_MAINTAINER_MODE=1 \
                    -DCMAKE_BUILD_TYPE=Debug"
else
  CMAKE_BUILD_TYPE="-DWITH_DEBUG=0 \
                    -DWITH_ASAN=0"
fi

cmake ../mysql-server/ \
  $CMAKE_BUILD_TYPE \
  -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON \
  -DWITH_SYSTEM_LIBS=0 \
  -DWITH_UNIT_TESTS=0 \
  -DWITH_ROUTER=0 \
  -DWITH_AUTHENTICATION_FIDO=0 \
  -DWITH_NDB=0 \
  -DWITH_ZLIB=bundled \
  -DDOWNLOAD_BOOST=1 \
  -DWITH_BOOST=~/mysql/boost \
  -DWITH_ASAN=0 \
  -DWITH_NDBCLUSTER_STORAGE_ENGINE=0 \
  -DWITH_ICU=system \
  -GNinja

echo "Running ninja"
# Defaults to 4 threads (-j4). More threads require more RAM (> 16 GB).
ninja -j$NINJA_THREADS

echo "Done building MySQL"

INIT_SERVER="~/mysql/${BUILD_DIR}/runtime_output_directory/mysqld --datadir=${DATA_DIR} --initialize-insecure"
RUN_SERVER="~/mysql/${BUILD_DIR}/runtime_output_directory/mysqld --datadir=${DATA_DIR}"
RUN_CLIENT="~/mysql/${BUILD_DIR}/runtime_output_directory/mysql -uroot"

printf "\n**********\n"
printf "Initialize server:\n  ${INIT_SERVER}\n"
printf "Run server:\n  ${RUN_SERVER}\n"
printf "Run client:\n  ${RUN_CLIENT}\n"
