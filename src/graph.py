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

# Filter the data to include only those with 'data_size' equals to 1000000.
df = df[df["data_size"] == 1000000]

# Identify the ICU configuration and add it to a new column
df["ICU_config"] = df.apply(identify_icu_config, axis=1)

"""
Calculate median of 'order_by_asc', 'order_by_desc' and 'equals' for each
configuration, as well as the standard deviation.
"""
df_stats = (
    df.groupby(["locale", "ICU_config", "collation", "data_size"])
    .agg(
        {
            "order_by_asc": ["median", "std"],
            "order_by_desc": ["median", "std"],
            "equals": ["median", "std"],
        }
    )
    .reset_index()
)


# Join all multi-level columns (i.e. ["order_by_asc", "median"] etc)
df_stats.columns = [
    f"{x[0]}_{x[1]}" if x[1] else x[0] for x in df_stats.columns.ravel()
]


# Debugging only: show all data in the dataframe
# pd.set_option("display.max_columns", None)
# print(df_stats.describe())
# print(df_stats.info())
# print(df_stats.sample(10))

# Set destination folder for plots
plot_dir = os.path.join("..", "plots", "experiment1")

# Create the directory if it doesn't exist
os.makedirs(plot_dir, exist_ok=True)

for metric in ["order_by_asc", "order_by_desc", "equals"]:
    for group in COLLATIONS[:2]:
        df_group = df_stats[
            (df_stats["collation"].isin([group["icu"], group["mysql"]]))
            & (df_stats["locale"] == group["locale"])
            & (df_stats["data_size"] == 1000000)
        ]

        # Debugging only: show all data in the dataframe
        # pd.set_option("display.max_columns", None)
        # print(df_group.describe())
        # print(df_group.info())
        # print(df_group.sample(4))

        # Create plot with error bars
        plt.figure(figsize=(10, 6))
        median_column = f"{metric}_median"
        std_column = f"{metric}_std"
        sns.barplot(
            data=df_group,
            x="ICU_config",
            y=(median_column),
            yerr=df_group[std_column],
        )

        # Add title and label
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
