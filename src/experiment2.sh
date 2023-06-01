#!/bin/bash
# This script runs the flamegraph experiment for all collations in sequence

pid=""

# Define usage function
usage() {
  echo "Usage: $0 [-p PID] [-h]"
  echo "  -p PID: Specify the PID of the running MySQL server"
  echo "  -h: Display this help message"
  echo "Example: $0 -p 1234"
}

# Parse command line arguments
while getopts "p:h" opt; do
  case ${opt} in
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

# Check that PID is set
if [[ -z $pid ]]; then
  echo "Error: the PID (-p) parameter is required." >&2
  usage
  exit 1
fi

# Check that the server is running
python3 ~/mysql/src/cli.py test

# Execute the test for each collation
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_en_US_ai_ci -l "en_US"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_en_US_as_cs -l "en_US"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_nb_NO_ai_ci -l "nb_NO"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_fr_FR_ai_ci -l "fr_FR"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_zh_Hans_as_cs -l "zh_Hans"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_ja_JP_as_cs -l "ja_JP"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_icu_ja_JP_as_cs_ks -l "ja_JP"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_0900_ai_ci -l "en_US"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_0900_as_cs -l "en_US"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_nb_0900_ai_ci -l "nb_NO"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_zh_0900_as_cs -l "zh_Hans"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_ja_0900_as_cs -l "ja_JP"
bash ~/mysql/src/perf.sh -p $pid -c utf8mb4_ja_0900_as_cs_ks -l "ja_JP"
