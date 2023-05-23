import os
import pandas as pd
from migrate import make_migration
from pathlib import Path
from db import Connector
from utils.custom_logger import log
from tqdm import tqdm

LOCALES = ["en_US", "zh_Hans", "fr_FR", "nb_NO", "ja_JP"]
DATASET_SIZES = [100000, 1000000, 10000000]


def create_locale_table(locale: str):
    """Create a table for a given locale."""
    table_name = f"country_list_{locale}"
    statement = f"""
    -- sql
    CREATE TABLE {table_name} (
        id VARCHAR(64) NOT NULL,
        value VARCHAR(64) NOT NULL,
        PRIMARY KEY(id)
        )
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
    """
    return statement


def create_locale_tables_migration():
    """Create a migration file for all the locale tables we need to set up."""
    description = "Create tables for all locales (raw data)"
    migration_statement = ""
    for locale in LOCALES:
        migration_statement += create_locale_table(locale)
    make_migration(description=description, sql=migration_statement)


def get_locale_data(locale: str):
    """Read the CSV file for the given locale and return a list of tuples."""
    # Find the path to the CSV file
    root = Path(__file__).parent.parent
    data_folder = os.path.join(root, "data", "country-list", "data", locale)
    data_path = os.path.join(data_folder, "country.csv")

    # Read the CSV file into a pandas DataFrame, with "NaN" filtering disabled.
    # This is because Pandas interprets "NA" (Namibia) as NaN
    df = pd.read_csv(data_path, na_filter=False)

    # Insert all data into the table in a single operation
    tuples = list(df.itertuples(index=False, name=None))
    return tuples


def insert_locale_data(locale: str):
    """Insert data from the CSV file for this locale."""
    conn = Connector()
    table_name = f"country_list_{locale}"

    log.debug(f"Truncating table {table_name}")
    conn.cursor.execute(f"TRUNCATE TABLE IF EXISTS {table_name};")

    log.debug(f"Inserting data for {locale=}")
    statement = f"""
    -- sql
    INSERT INTO {table_name} (id, value) VALUES (%s, %s)
    ;
    """
    tuples = get_locale_data(locale)
    conn.cursor.executemany(statement, tuples)
    conn.connection.commit()
    log.debug(f"Finished inserting {len(tuples)} rows for {locale=}")


def insert_all_locale_data():
    """
    Insert test data from all CSV files into the database.
    This consists of the raw data from the country-list repo.
    """
    for locale in LOCALES:
        insert_locale_data(locale)


def create_test_tables():
    """Create tables required for performance testing."""
    for locale in LOCALES:
        for size in DATASET_SIZES:
            create_synthetic_test_table(locale, size)


def create_synthetic_test_table(locale: str, min_size: int):
    """
    Create a table of test data for benchmarking.
    Use the country list data for the given locale as a
    base, then expand it synthetically to the given size.
    """
    base_data = get_locale_data(locale)
    duplicates = (min_size // len(base_data)) + 1
    log.info(f"Creating test data for locale {locale}")
    log.debug(f"Base data has {len(base_data)} rows")
    log.debug(f"Minimum number of records: {min_size}")
    log.debug(f"Duplicates required: {duplicates} times")
    log.debug(f"Total rows to create: {duplicates * len(base_data)}")

    table_name = f"test_{locale}_{min_size}"
    conn = Connector()

    # Drop the table and recreate if it already exists
    conn.cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    conn.connection.commit()

    statement = f"""
    -- sql
    CREATE TABLE {table_name} (
        id VARCHAR(64) NOT NULL,
        value VARCHAR(64) NOT NULL,
        PRIMARY KEY(id)
        );
    """
    conn.cursor.execute(statement)
    conn.connection.commit()
    log.info(f"Created table {table_name}")

    insert = f"INSERT INTO {table_name} (id, value) VALUES (%s, %s);"
    for i in tqdm(range(duplicates)):
        new_tuples = [(row[0] + str(i), row[1] + str(i)) for row in base_data]
        conn.cursor.executemany(insert, new_tuples)
    conn.connection.commit()


if __name__ == "__main__":
    """
    This script is run once to generate the migrations we need to set up tables
    for the raw test data (i.e. the data we get from the country-list repo).
    """
    create_locale_tables_migration()
