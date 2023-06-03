"""
This file is used for creating plots/graphs/tables from the performance benchmark.
Copy the SQLite database from the test bench computer and rename it to
"final_results.db" before running this file.

Debugging tricks:
# pd.set_option("display.max_columns", None)
# print(df.describe())
# print(df.info())
# print(df.sample(10))
# print(df.columns)
"""
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate

# Column name for the build configuration tested
ICU_CONFIG = "Collation system"
CONFIGURATIONS = ["MySQL", "ICU_default", "ICU_frozen", "ICU_tailored"]

# Set destination folder for plots
PLOT_DIR = os.path.join("..", "results", "experiment1")

# Define common parameters for all plots
plt.rc("font", size=14)  # controls default text sizes
plt.rc("axes", titlesize=20)  # fontsize of the axes title
plt.rc("axes", labelsize=16)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=14)  # fontsize of the tick labels
plt.rc("ytick", labelsize=14)  # fontsize of the tick labels
plt.rc("legend", fontsize=14)  # legend fontsize
plt.rc("figure", titlesize=22)  # fontsize of the figure title
PLOT_PARAMS = {
    "errorbar": "sd",  # Standard deviation
    "capsize": 0.2,  # Cap size for error bars
    "errwidth": 3,  # Width of error bars
}


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


def parse_data() -> pd.DataFrame:
    """Parse the data from the SQLite database and return a dataframe."""

    # Connect to the database
    conn = sqlite3.connect("../final_results.db")

    # Fetch the data from the SQLite database
    query = "SELECT * FROM benchmarks"
    df = pd.read_sql_query(query, conn)

    # Identify the ICU configuration and add it to a new column
    df[ICU_CONFIG] = df.apply(identify_icu_config, axis=1)

    # Filter the data to include only those with 'data_size' equals to 1000000.
    df_stats = df[df["data_size"] == 1000000]

    return df_stats


# Create the directory if it doesn't exist
os.makedirs(PLOT_DIR, exist_ok=True)

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
    destination = os.path.join(PLOT_DIR, f"{name}.tex")
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


def create_plot(df: pd.DataFrame, metric: str, groups: list[dict]):
    """Create a plot containing 4 subplots."""
    assert len(groups) == 4

    latex_subplots = []
    plot_filename = f"experiment1_{metric}"
    plot_label = f"experiment1_{metric}"

    # flake8: noqa (this line just needs to be a long, single line)
    plot_caption = f"Comparing execution time for the {metric_names[metric]} operation across various collations. Lower execution time is better. Error bars show standard deviation. These collations are all accent-, case- and (where applicable) kana-insensitive"

    for group in groups:
        df_group = df[
            (df["collation"].isin([group["icu"], group["mysql"]]))
            & (df["locale"] == group["locale"])
            & (df["data_size"] == 1000000)
        ]

        # Sort values alphabetically, so we get MySQL last every time
        df_group = df_group.sort_values(ICU_CONFIG)

        # Create plot with error bars
        plt.figure(figsize=(10, 6))

        sns.barplot(
            x=ICU_CONFIG, y=metric, data=df_group, estimator=np.median, **PLOT_PARAMS
        )

        # Add title and label
        plt.title(f"Median execution time for operation '{metric}'")
        plt.ylabel("Time (s)")

        # Define the destination for the plot and tex file
        file_name = f"{group['locale']}_{group['icu']}_vs_{group['mysql']}_{metric}"
        destination = os.path.join(
            PLOT_DIR,
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


def create_plots():
    """Create all plots."""
    # Filter on the metrics we want to plot
    plot_metrics = ["order_by_asc", "equals"]

    # The subset of tested collations we want to plot
    plot_collations = [
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

    df = parse_data()
    for metric in plot_metrics:
        create_plot(df, metric, plot_collations)


def summarize_data() -> pd.DataFrame:
    """Create a table of all the results."""
    df = parse_data()

    # Columns which do not need to be included in the table
    ignored_columns = [
        "id",
        "ICU_FROZEN",
        "ICU_EXTRA_TAILORING",
        "data_size",
        "data_table",
    ]

    # Remove the ignored columns
    df = df.drop(columns=ignored_columns)

    # Aggregate the data on 'collation' and 'locale' and calculate the median
    df_median = (
        df.groupby(["collation", "locale", ICU_CONFIG])
        .agg(
            order_by_asc_median=("order_by_asc", "median"),
            order_by_desc_median=("order_by_desc", "median"),
            equals_median=("equals", "median"),
            count=("collation", "size"),
        )
        .reset_index()
    )

    # Calculate the standard deviation
    df_std = (
        df.groupby(["collation", "locale", ICU_CONFIG])
        .agg(
            order_by_asc_std=("order_by_asc", np.std),
            order_by_desc_std=("order_by_desc", np.std),
            equals_std=("equals", np.std),
        )
        .reset_index()
    )

    # Merge the median and standard deviation dataframes
    df = pd.merge(df_median, df_std, on=["collation", "locale", ICU_CONFIG])
    df = df.reset_index(drop=True)

    # Choose a baseline row which will be used for comparing the other rows
    baseline = df[
        (df["collation"] == "utf8mb4_0900_ai_ci")
        & (df["locale"] == "en_US")
        & (df[ICU_CONFIG] == "MySQL")
    ]

    # For each relevant column, calculate the difference from the baseline in percent
    for column in [
        "order_by_asc_median",
        "order_by_desc_median",
        "equals_median",
    ]:
        baseline_value = baseline[column].values[0]
        df[column + "_diff_percent"] = (
            (df[column] - baseline_value) / baseline_value
        ) * 100

    # Round the values and convert to string, to ensure 2 decimals
    for col in [
        "order_by_asc_median",
        "order_by_desc_median",
        "equals_median",
        "order_by_asc_std",
        "order_by_desc_std",
        "equals_std",
        "order_by_asc_median_diff_percent",
        "order_by_desc_median_diff_percent",
        "equals_median_diff_percent",
    ]:
        df[col] = df[col].apply(lambda x: f"{x:.2f}")

    # Order the data by config/col/locale
    df = df.sort_values(by=[ICU_CONFIG, "locale", "collation"])
    return df


def create_latex_table(content: str, label: str, caption: str) -> str:
    """Create a LaTeX table."""
    # Remove the two first lines of the content so we can replace the header
    split_content = content.split("\n")[2:]
    content = "\n".join(split_content)

    # \begin{{tabular}}{{llp{{2cm}}p{{2cm}}p{{2cm}}}}
    # Collation & Locale & Time (s) & Std. dev. (s) & Diff. from baseline (\%) \\\\
    table = f"""
    \\begin{{table}}[htp]
    \\centering
    \\begin{{tabular}}{{llrrr}}
    \\toprule
    \\thead{{Collation}} & 
    \\thead{{Locale}} & 
    \\thead{{Time \\\\ (s)}} & 
    \\thead{{Std. dev \\\\ (s)}} & 
    \\thead{{$\Delta$ baseline \\\\ (\%)}} \\\\
    \\midrule
    {content}
    \\caption{{{caption}}}
    \\label{{tab:{label}}}
    \\end{{table}}
    """
    return table


def filter_asc_table(df: pd.DataFrame) -> str:
    """Filter the data to only include the order by asc section."""
    # Rename columns to human readable format
    C1 = "thead{Execution // time (s)}"
    df = df.rename(
        columns={
            "order_by_asc_median": C1,
            "order_by_asc_std": "Std. dev. (s)",
            "order_by_asc_median_diff_percent": "Diff. from baseline (%)",
        }
    )

    # Specify the columns to print and their order
    columns_to_print = [
        "Collation",
        "Locale",
        C1,
        "Std. dev. (s)",
        "Diff. from baseline (%)",
    ]

    # Convert the dataframe to a list of lists to remove ID column
    df_asc = df[columns_to_print].values.tolist()

    # Create LaTeX table content and return it
    return tabulate(df_asc, tablefmt="latex_booktabs")


def filter_desc_table(df: pd.DataFrame) -> str:
    """Filter the data to only include the order by desc section."""
    # Rename columns to human readable format
    df = df.rename(
        columns={
            "order_by_desc_median": "Execution time (s)",
            "order_by_desc_std": "Std. dev. (s)",
            "order_by_desc_median_diff_percent": "Diff. from baseline (%)",
        }
    )

    # Specify the columns to print and their order
    columns_to_print = [
        "Collation",
        "Locale",
        "Execution time (s)",
        "Std. dev. (s)",
        "Diff. from baseline (%)",
    ]

    # Convert the dataframe to a list of lists to remove ID column
    df_desc = df[columns_to_print].values.tolist()

    # Create LaTeX table content and return it
    return tabulate(df_desc, tablefmt="latex_booktabs")


def filter_equals_table(df: pd.DataFrame) -> str:
    """Filter the data to only include the equals section."""
    # Rename columns to human readable format
    df = df.rename(
        columns={
            "equals_median": "Execution time (s)",
            "equals_std": "Std. dev. (s)",
            "equals_median_diff_percent": "Diff. from baseline (%)",
        }
    )

    # Specify the columns to print and their order
    columns_to_print = [
        "Collation",
        "Locale",
        "Execution time (s)",
        "Std. dev. (s)",
        "Diff. from baseline (%)",
    ]

    # Convert the dataframe to a list of lists to remove ID column
    df_equals = df[columns_to_print].values.tolist()

    # Create LaTeX table content and return it
    return tabulate(df_equals, tablefmt="latex_booktabs")


def generate_latex_tables():
    """Save the tables of results as LaTeX files."""
    df = summarize_data()
    df = df.rename(
        columns={
            "collation": "Collation",
            ICU_CONFIG: "Configuration",
            "locale": "Locale",
        }
    )

    # Define a file for the main output (all tables)
    main_output_file = "experiment1_results.tex"
    destination = os.path.join(PLOT_DIR, main_output_file)

    # Delete the file if it already exists
    if os.path.exists(destination):
        os.remove(destination)

    # Split the dataframe into one for each configuration
    for c in CONFIGURATIONS:
        sub_df = df[df["Configuration"] == c]

        asc_content = filter_asc_table(sub_df)
        asc_caption = f"ORDER BY ASC for all {c} collations.".replace("_", "\\_")
        asc_table = create_latex_table(asc_content, f"experiment1_{c}_asc", asc_caption)

        desc_content = filter_desc_table(sub_df)
        desc_caption = f"ORDER BY DESC for all {c} collations.".replace("_", "\\_")
        desc_table = create_latex_table(
            desc_content, f"experiment1_{c}_desc", desc_caption
        )

        equals_content = filter_equals_table(sub_df)
        equals_caption = f"Equality comparison for all {c} collations.".replace(
            "_", "\\_"
        )
        equals_table = create_latex_table(
            equals_content, f"experiment1_{c}_equals", equals_caption
        )

        # Append the tables to the main output file
        with open(destination, "a") as f:
            f.write(asc_table)
            f.write(desc_table)
            f.write(equals_table)


def generate_size_comparison_table():
    """Generate a small table which shows the effect of differently sized data sets."""

    def get_size_comparison_data():
        """Read raw data from SQLite into a dataframe."""
        # Connect to the database
        conn = sqlite3.connect("../final_results.db")
        query = """
        SELECT collation, ICU_FROZEN, ICU_EXTRA_TAILORING, locale, data_size,
          (AVG(order_by_asc) *  100000) / data_size AS avg_order_by
        FROM benchmarks 
        GROUP BY  collation, ICU_FROZEN, ICU_EXTRA_TAILORING, locale, data_size
        ORDER BY avg_order_by ASC;
        """
        df = pd.read_sql_query(query, conn)
        df[ICU_CONFIG] = df.apply(identify_icu_config, axis=1)

        # Drop the ICU_FROZEN and ICU_EXTRA_TAILORING columns
        df = df.drop(columns=["ICU_FROZEN", "ICU_EXTRA_TAILORING"])
        return df

    df = get_size_comparison_data()

    # Transform 'data_size' to represent thousands for readability
    df["data_size"] = (df["data_size"] / 1000).round().astype(int)

    # Get unique values from 'data_size' column and sort them
    categories = sorted(df["data_size"].unique())

    # Convert the data_size column to categorical so it will maintain the order
    df["data_size"] = pd.Categorical(
        df["data_size"], categories=categories, ordered=True
    )

    # Create a bar plot for median with error bars representing std
    plt.figure(figsize=(10, 6))
    sns.barplot(
        x="data_size", y="avg_order_by", data=df, estimator=np.median, **PLOT_PARAMS
    )

    plt.xlabel("Size of data set (in thousands)")
    plt.ylabel("Execution time (s)")
    plt.title("Median execution time per 100K rows")

    # Save the plot to the file
    destination = os.path.join(
        PLOT_DIR,
        "size_comparison.png",
    )
    plt.savefig(destination)
    plt.close()


create_plots()
generate_latex_tables()

generate_size_comparison_table()
