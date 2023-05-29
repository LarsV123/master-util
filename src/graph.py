"""
This file is to be used for creating plots/graphs from the performance benchmark.
Copy the SQLite database from the test bench computer and rename it to
"final_results.db" before running this file.
"""
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from benchmarks import COLLATIONS


def identify_icu_config(row):
    """Identify the configuration tested."""
    if not row["collation"].startswith("utf8mb4_icu"):
        return "MySQL"
    elif row["ICU_EXTRA_TAILORING"]:
        return "ICU_tailored"
    elif row["ICU_FROZEN"]:
        return "ICU_frozen"
    else:
        return "ICU_default"


# Connect to the database
conn = sqlite3.connect("../final_results.db")


# Fetch the data from the SQLite database
query = "SELECT * FROM benchmarks"
df = pd.read_sql_query(query, conn)

# Identify the ICU configuration and add it to a new column
df["ICU_config"] = df.apply(identify_icu_config, axis=1)

# Calculate the median over the 10 runs for each configuration
df_median = (
    df.groupby(["locale", "ICU_config", "collation", "data_size"])[
        ["order_by_asc", "order_by_desc", "equals"]
    ]
    .median()
    .reset_index()
)

# Filter the data to include only those with 'data_size' equals to 1000000.
df_median = df_median[df_median["data_size"] == 1000000]

# Set destination folder for plots
plot_dir = os.path.join("..", "plots", "experiment1")

# Create the directory if it doesn't exist
os.makedirs(plot_dir, exist_ok=True)

for group in COLLATIONS[:1]:
    # Filter the data for the current group
    df_group = df_median[
        (
            (df_median["collation"] == group["icu"])
            | (df_median["collation"] == group["mysql"])
        )
        & (df_median["locale"] == group["locale"])
    ]

    df_median = df_group.groupby(["ICU_config"])[
        ["order_by_asc", "order_by_desc", "equals"]
    ]

    # For each metric, create a bar plot.
    for metric in ["order_by_asc", "order_by_desc", "equals"]:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df_group, x="ICU_config", y=metric)
        plt.title(f"Median execution time for operation '{metric}'")
        plt.ylabel("Time (s)")

        # Define the full file path
        file_path = os.path.join(
            plot_dir,
            f'{group["locale"]}_{group["icu"]}_vs_{group["mysql"]}_{metric}.png',
        )

        # Save the plot to the file
        plt.savefig(file_path)
        plt.close()
