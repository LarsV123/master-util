#!/bin/bash

# Initialize variables
collation=""
pid=""
locale=""

# Define usage function
usage() {
  echo "Usage: $0 [-c COLLATION] [-p PID] [-h]"
  echo "  -c COLLATION: Specify the COLLATION to test"
  echo "  -p PID: Specify the PID of the running MySQL server"
  echo "  -h: Display this help message"
  echo "Example: $0 -c utf8mb4_0900_ai_ci -p 1234"
}

# Parse command line arguments
while getopts "c:p:l:h" opt; do
  case ${opt} in
  c)
    collation=${OPTARG}
    ;;
  p)
    pid=${OPTARG}
    ;;
  l)
    locale=${OPTARG}
    ;;
  h)
    usage
    exit 0
    ;;
  \?)
    echo "Invalid option: -$OPTARG" >&2
    usage
    exit 1
    ;;
  :)
    echo "Option -$OPTARG requires an argument." >&2
    usage
    exit 1
    ;;
  esac
done

# Check that all parameters are present
if [[ -z $collation || -z $pid || -z $locale ]]; then
  echo "Error: All parameters are required." >&2
  usage
  exit 1
fi

# Define function to print input variables
print_input_variables() {
  echo "COLLATION: $collation"
  echo "PID: $pid"
  echo "LOCALE: $locale"
}

# Define background processing function
background_processing() {
  echo "Running background processing with parameters:"
  echo "  COLLATION: $collation"
  echo "  PID: $pid"
  echo "  LOCALE: $locale"
  perf record -p $pid -F 4000 -g -- sleep 30
  perf script | ~/mysql/flamegraph/stackcollapse-perf.pl >out.perf-folded
  ~/mysql/flamegraph/flamegraph.pl out.perf-folded >"${collation}.svg"
  echo "Background processing complete."
}

# Check our input variables
print_input_variables

# Do a warm-up run first, so the collation is loaded into memory
python3 ~/mysql/src/cli.py stresstest -c $collation -l $locale -i 1

# Run background processing in a separate thread
background_processing &

# Generate data for perf to record
python3 ~/mysql/src/cli.py stresstest -c $collation -l $locale

# Wait for background processing to complete
wait
