import os
import pandas as pd
from migrate import make_migration
from pathlib import Path
from db import Connector
from utils.custom_logger import log
from tqdm import tqdm

locales = ["en_US", "th_TH", "zh_Hans", "uk_UA", "fr_FR", "no_NO", "ja_JP"]


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
    for locale in locales:
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
    """Insert data from the CSV file for this locale"""
    log.debug(f"Inserting data for {locale=}")
    table_name = f"country_list_{locale}"
    statement = f"""
    -- sql
    INSERT INTO {table_name} (id, value) VALUES (%s, %s)
    ;
    """
    tuples = get_locale_data(locale)
    conn = Connector()
    conn.cursor.executemany(statement, tuples)
    conn.connection.commit()
    log.debug(f"Finished inserting {len(tuples)} rows for {locale=}")


def insert_all_locale_data():
    """
    Insert test data from all CSV files into the database.
    This consists of the raw data from the country-list repo.
    """
    for locale in locales:
        insert_locale_data(locale)


def create_temp_test_table():
    """
    Create a table of synthetic data for testing purposes.
    Use Norwegian data as input, and use numeric suffixes to expand the data set.
    """
    conn = Connector()
    table_name = "test1_no_NO"
    duplicates = 1000

    # Drop the table and recreate if it already exists
    conn.cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    conn.connection.commit()

    statement = f"""
    -- sql
    CREATE TABLE {table_name} (
        id VARCHAR(64) NOT NULL,
        value VARCHAR(64) NOT NULL,
        PRIMARY KEY(id)
        )
    COLLATE utf8mb4_nb_icu_ai_ci;
    """
    conn.cursor.execute(statement)
    conn.connection.commit()
    log.info(f"Created table {table_name}")

    tuples = get_locale_data("no_NO")
    log.info(f"Inserting {len(tuples)} unique values into {table_name}")
    log.info(f"Each value is duplicated {duplicates} times by adding a suffix")

    insert = f"INSERT INTO {table_name} (id, value) VALUES (%s, %s);"
    for i in tqdm(range(1, duplicates)):
        new_tuples = [(row[0] + str(i), row[1] + str(i)) for row in tuples]
        conn.cursor.executemany(insert, new_tuples)
    conn.connection.commit()
    return table_name


if __name__ == "__main__":
    """
    This script is run once to generate the migrations we need to set up tables
    for the raw test data (i.e. the data we get from the country-list repo).
    """
    create_locale_tables_migration()
