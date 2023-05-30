"""
This file is to be used for creating plots/graphs from the performance benchmark.
Copy the SQLite database from the test bench computer and rename it to
"final_results.db" before running this file.
"""
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


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
ICU_CONFIG = "Collation system"
df[ICU_CONFIG] = df.apply(identify_icu_config, axis=1)

# Filter the data to include only those with 'data_size' equals to 1000000.
df_stats = df[df["data_size"] == 1000000]


# Debugging only: show all data in the dataframe
# pd.set_option("display.max_columns", None)
# print(df_stats.describe())
# print(df_stats.info())
# print(df_stats.sample(10))

# Set destination folder for plots
plot_dir = os.path.join("..", "plots", "experiment1")

# Create the directory if it doesn't exist
os.makedirs(plot_dir, exist_ok=True)

# Map the metric to a human-readable name
metric_names = {
    "order_by_asc": "ORDER BY ASC",
    "order_by_desc": "ORDER BY DESC",
    "equals": "equality comparison",
}

# Map the locale to a human-readable name
locale_names = {
    "en_US": "English",
    "nb_NO": "Norwegian Bokmål",
    "fr_FR": "French",
    "ja_JP": "Japanese",
    "zh_Hans": "Simplified Chinese",
}


def save_latex_plot_wrapper(name: str, label: str, caption: str, subplots: list[str]):
    """Save a .tex file with 4 subplots."""
    assert len(subplots) == 4

    # Delete the file if it already exists
    destination = os.path.join(plot_dir, f"{name}.tex")
    if os.path.exists(destination):
        os.remove(destination)

    # Create the wrapper
    wrapper = f"""
    \\begin{{figure}}[htp]
    \\centering
    {subplots[0]}
    \\hfill
    {subplots[1]}
    \\par
    {subplots[2]}
    \\hfill
    {subplots[3]}
    \\caption{{{caption}}}
    \\label{{fig:{label}}}
    \\end{{figure}}
    """
    with open(destination, "w") as f:
        f.write(wrapper)


def create_subplot_wrapper(filename: str, metric: str, group: dict) -> str:
    """Create a LaTeX wrapper for a subplot."""
    print(f"Creating LaTeX wrapper for subplot {filename}")

    locale = group["locale"]
    plot_folder = "img/experiment1/"
    caption = f"{locale_names[locale]} ({locale})"
    label = f"fig:experiment1_{metric}_{filename}"

    # Sanitize for latex, replacing underscores with \_
    caption = caption.replace("_", "\\_")

    return f"""\\begin{{subfigure}}{{.45\\textwidth}}
                \\centering
                \\includegraphics[width=\\textwidth]{{{plot_folder}{filename}.png}}
                \\label{{{label}}}
                \\caption{{{caption}}}
            \\end{{subfigure}}"""


def create_plot(metric: str, groups: list[dict]):
    """Create a plot containing 4 subplots."""
    assert len(groups) == 4

    latex_subplots = []
    plot_filename = f"experiment1_{metric}"
    plot_label = f"experiment1_{metric}"
    plot_caption = f"Comparing execution time for the {metric_names[metric]} operation across various collations. Lower execution time is better. Error bars show standard deviation. These collations are all accent-, case- and (where applicable) kana-insensitive"

    for group in COLLATIONS:
        df_group = df_stats[
            (df_stats["collation"].isin([group["icu"], group["mysql"]]))
            & (df_stats["locale"] == group["locale"])
            & (df_stats["data_size"] == 1000000)
        ]

        # Sort values alphabetically, so we get MySQL last every time
        df_group = df_group.sort_values(ICU_CONFIG)

        # Create plot with error bars
        plt.figure(figsize=(10, 6))

        sns.barplot(
            x=ICU_CONFIG,
            y=metric,
            data=df_group,
            estimator=np.median,
            errorbar="sd",  # Standard deviation
            capsize=0.2,
        )

        # Add title and label
        plt.title(
            f"Median execution time for operation '{metric}'. Error bars show std. deviation."
        )
        plt.ylabel("Time (s)")

        # Define the destination for the plot and tex file
        file_name = f"{group['locale']}_{group['icu']}_vs_{group['mysql']}_{metric}"
        destination = os.path.join(
            plot_dir,
            f"{file_name}.png",
        )

        # Save the plot to the file
        plt.savefig(destination)
        plt.close()

        # Create a LaTeX wrapper for the plot
        subplot = create_subplot_wrapper(file_name, metric, group)
        latex_subplots.append(subplot)

    # Save the LaTeX wrapper for the plot
    save_latex_plot_wrapper(
        subplots=latex_subplots,
        name=plot_filename,
        label=plot_label,
        caption=plot_caption,
    )


# Filter on the metrics we want to plot
plot_metrics = ["order_by_asc", "equals"]

# The subset of tested collations we want to plot
COLLATIONS = [
    {
        "icu": "utf8mb4_icu_en_US_ai_ci",
        "mysql": "utf8mb4_0900_ai_ci",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_nb_NO_ai_ci",
        "mysql": "utf8mb4_nb_0900_ai_ci",
        "locale": "nb_NO",
    },
    {
        "icu": "utf8mb4_icu_zh_Hans_as_cs",
        "mysql": "utf8mb4_zh_0900_as_cs",
        "locale": "zh_Hans",
    },
    {
        "icu": "utf8mb4_icu_ja_JP_as_cs_ks",
        "mysql": "utf8mb4_ja_0900_as_cs_ks",
        "locale": "ja_JP",
    },
]

for metric in plot_metrics:
    create_plot(metric, COLLATIONS)
