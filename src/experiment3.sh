#!/bin/bash
# This script runs all validity tests for experiment 3
# Values are hardcoded, as there's no need to change them
# on the fly.

# Define connection parameters
p1=3306
p2=3307

# python3 ~/mysql/src/cli.py validate -p1 $p1 -p2 $p2 -c1 utf8mb4_icu_en_US_ai_ci -c2 "utf8mb4_icu_en_US_ai_ci"

# Define an array of all collations to test
collations=("utf8mb4_0900_ai_ci" "utf8mb4_icu_en_US_ai_ci" "utf8mb4_icu_en_US_as_cs" "utf8mb4_icu_nb_NO_ai_ci" "utf8mb4_icu_fr_FR_ai_ci" "utf8mb4_icu_zh_Hans_as_cs" "utf8mb4_icu_ja_JP_as_cs" "utf8mb4_icu_ja_JP_as_cs_ks")

# Print the full array before starting
echo "Collations which will be tested:"
for collation in "${collations[@]}"; do
  echo $collation
done
echo

# Iterate over the array
for collation in "${collations[@]}"; do
  python3 ~/mysql/src/cli.py validate -p1 $p1 -p2 $p2 -c1 $collation -c2 $collation
done
