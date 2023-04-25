#!/bin/bash

# Initialize variables
collation=""
pid=""

# Define usage function
usage() {
  echo "Usage: $0 [-c COLLATION] [-p PID] [-h]"
  echo "  -c COLLATION: Specify the COLLATION to test"
  echo "  -p PID: Specify the PID of the running MySQL server"
  echo "  -h: Display this help message"
  echo "Example: $0 -c utf8mb4_0900_ai_ci -p 1234"
}

# Parse command line arguments
while getopts "c:p:h" opt; do
  case ${opt} in
  c)
    collation=${OPTARG}
    ;;
  p)
    pid=${OPTARG}
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

# Check that both parameters are present
if [[ -z $collation || -z $pid ]]; then
  echo "Error: both COLLATION (-c) and PID (-p) parameters are required." >&2
  usage
  exit 1
fi

# Define function to print input variables
print_input_variables() {
  echo "COLLATION: $collation"
  echo "PID: $pid"
}

# Define background processing function
background_processing() {
  echo "Running background processing with parameters:"
  echo "  COLLATION: $collation"
  echo "  PID: $pid"
  perf record -p 14147 -F 4000 -g -- sleep 30
  echo "Background processing complete."
}

# Check our input variables
print_input_variables

# Run background processing in a separate thread
background_processing &

# Generate data for perf to record
python3 src/cli.py stresstest -c $collation

# Wait for background processing to complete
wait
