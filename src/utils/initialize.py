"""
This file contains utility functions for initializing the database,
to prepare everything needed for running benchmarks.
This includes creating tables and inserting test data.
"""

import os
import pandas as pd
from pathlib import Path
from db import Connector
from utils.custom_logger import log
from tqdm import tqdm


LOCALES = ["en_US", "zh_Hans", "fr_FR", "nb_NO", "ja_JP"]
DATASET_SIZES = [500_000, 1_000_000, 2_500_000]


def prepare_performance_benchmarks():
    """
    Prepare the database for running performance benchmarks.
    For this we need to:
    - Read and insert sample data from the country-list repo
    - Synthetically expand this data to the required size
    - Create a separate table for each locale and dataset size
    """
    conn = Connector()
    log.info(
        "Preparing test data for performance benchmarks. This could take a while..."
    )

    for locale in LOCALES:
        log.info(f"Preparing data for {locale=}")
        create_base_locale_table(conn, locale)
        fill_base_locale_table(conn, locale)
        for size in DATASET_SIZES:
            log.info(f"Preparing data for {locale=} and {size=}")
            create_expanded_locale_table(conn, locale, size)

    conn.close()
    log.info("Finished preparing test data for performance benchmarks.")


def prepare_validity_tests():
    """
    Prepare the database for running validity tests.
    This includes:
    - Creating a table of all valid Unicode characters
    - Creating a table of example strings which should be included in the test
    """
    conn = Connector()
    log.info("Preparing test data for validity tests...")
    create_unicode_table(conn)
    create_sample_strings_table(conn)
    conn.close()
    log.info("Finished preparing test data for validity tests.")


def create_base_locale_table(conn: Connector, locale: str):
    """Create a table with the base data for a locale."""
    table_name = f"country_list_{locale}"

    log.debug(f"Dropping table {table_name} if it already exists")
    statement = f"DROP TABLE IF EXISTS {table_name};"
    conn.cursor.execute(statement)
    conn.connection.commit()

    log.debug(f"Creating table {table_name}")
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


def fill_base_locale_table(conn: Connector, locale: str):
    """Insert data from the CSV file for this locale."""
    table_name = f"country_list_{locale}"

    log.debug(f"Truncating table {table_name}")
    conn.cursor.execute(f"TRUNCATE TABLE {table_name};")

    log.debug(f"Reading data for {locale=} from CSV file")
    tuples = get_locale_data(locale)

    log.debug(f"Inserting data for {locale=}")
    statement = f"""
    -- sql
    INSERT INTO {table_name} (id, value) VALUES (%s, %s)
    ;
    """
    conn.cursor.executemany(statement, tuples)
    conn.connection.commit()
    log.debug(f"Finished inserting {len(tuples)} rows for {locale=}")


def get_locale_data(locale: str):
    """Read the CSV file for the given locale and return a list of tuples."""
    # Find the path to the CSV file
    root = Path(__file__).parent.parent.parent
    data_folder = os.path.join(root, "data", "country-list", "data", locale)
    data_path = os.path.join(data_folder, "country.csv")

    # Read the CSV file into a pandas DataFrame, with "NaN" filtering disabled.
    # This is because Pandas interprets "NA" (Namibia) as NaN
    df = pd.read_csv(data_path, na_filter=False)

    return list(df.itertuples(index=False, name=None))


def create_expanded_locale_table(conn: Connector, locale: str, min_size: int):
    """
    Create a table with the expanded data for a locale.
    This is done by reading the base data and synthetically expanding it,
    creating a table with the given minimum size.
    """
    base_data = get_locale_data(locale)
    duplicates = (min_size // len(base_data)) + 1
    log.info(f"Creating test data for locale {locale}")
    log.debug(f"Base data has {len(base_data)} rows")
    log.debug(f"Minimum number of records: {min_size}")
    log.debug(f"Duplicates required: {duplicates} times")
    log.debug(f"Total rows to create: {duplicates * len(base_data)}")

    table_name = f"test_{locale}_{min_size}"
    log.debug(f"Dropping table {table_name} if it already exists")
    conn.cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    conn.connection.commit()

    log.debug(f"Creating table {table_name}")
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

    log.debug(f"Inserting data for {locale=}")
    insert = f"INSERT INTO {table_name} (id, value) VALUES (%s, %s);"
    for i in tqdm(range(duplicates)):
        new_tuples = [(row[0] + str(i), row[1] + str(i)) for row in base_data]
        conn.cursor.executemany(insert, new_tuples)
    conn.connection.commit()


def create_unicode_tuples() -> list[tuple[int, str, str]]:
    """
    Create a list of tuples of all characters in the Unicode range.
    Each tuple is on the form (codepoint, hex value of codepoint, character).
    """
    tuples: list[tuple[int, str, str]] = []

    for i in range(0, 0x10FFFF + 1):
        try:
            char = chr(i)
            tuples.append((i, str(hex(i)), char))
        except ValueError:
            # Some code points in the range are not valid Unicode characters
            pass
    log.info(f"Created {len(tuples)} Unicode characters.")
    return tuples


def create_unicode_table(conn: Connector):
    """Create a table with all valid Unicode characters."""
    table = "unicode_characters"
    log.debug(f"Dropping table {table} if it already exists")
    statement = f"DROP TABLE IF EXISTS {table};"
    conn.cursor.execute(statement)

    log.debug(f"Creating table {table}...")
    statement = f"""
    -- sql
    CREATE TABLE {table} (
      `code_point` INT PRIMARY KEY NOT NULL,
      `char_value` VARCHAR(255) NOT NULL,
      `hex_value` VARCHAR(32) NOT NULL
    );
    """
    conn.cursor.execute(statement)

    tuples = create_unicode_tuples()
    log.info(f"Inserting {len(tuples)} Unicode characters into the database...")
    statement = f"""
    -- sql
    INSERT INTO {table} (code_point, hex_value, char_value)
    VALUES (%s, %s, %s);
    """
    failures = []
    for i in tqdm(range(0, len(tuples))):
        try:
            conn.cursor.execute(statement, tuples[i])
        except Exception as e:
            log.debug(e)
            failures.append(tuples[i])
    log.info(f"Failed to insert {len(failures)} of {len(tuples)} characters.")
    conn.connection.commit()


def create_sample_strings_table(conn: Connector):
    """
    Create a table of additional strings to be used when comparing collations.
    For the purposes of this test, this is just a list of 2-character
    permutations of the Latin alphabet.
    """
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    strings = []
    for i in alphabet:
        for j in alphabet:
            strings.append(i + j)

    table = "sample_strings"
    log.debug(f"Dropping table {table} if it already exists")
    statement = f"DROP TABLE IF EXISTS {table};"
    conn.cursor.execute(statement)

    log.debug(f"Creating table {table}...")
    statement = f"""
    -- sql
    CREATE TABLE {table} (
    string VARCHAR(64) NOT NULL,
    PRIMARY KEY(string)
    );
    """
    conn.cursor.execute(statement)

    log.info(f"Inserting {len(strings)} sample strings into the database...")
    statement = f"INSERT INTO {table} (string) VALUES (%s);"
    for s in tqdm(strings):
        conn.cursor.execute(statement, (s,))
    conn.connection.commit()
