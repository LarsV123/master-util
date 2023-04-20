# Tools for validating that two collations produce the same results.

from tqdm import tqdm
from db import Connector
from utils.custom_logger import log

CODE_POINT_COUNT = 1_114_112


def get_unicode_tuples():
    """
    Create a list of tuples of all characters in the Unicode range.
    """
    count = 0
    # pbar = tqdm(total=CODE_POINT_COUNT)
    tuples: list[tuple[int, hex, str]] = []

    for i in range(0, 0x10FFFF):
        # pbar.update(1)
        try:
            char = chr(i)
            tuples.append((i, hex(i), char))
        except ValueError:
            # Some code points in the range are not valid Unicode characters
            pass
    return tuples


def insert_unicode_tuples():
    """Insert all Unicode characters into the database."""
    conn = Connector()
    tuples = get_unicode_tuples()
    statement = f"""
    -- sql
    INSERT INTO unicode_characters (code_point, hex_value, char_value) VALUES (%s, %s, %s)
    ;
    """
    # Insert the data in batches of 1 000 rows
    for i in tqdm(range(0, len(tuples), 1_000)):
        conn.cursor.executemany(statement, tuples[i : i + 1_000])
        conn.connection.commit()
    conn.close()


def get_max_codepoint():
    """
    Find the character with the highest code point in the Unicode range.
    """
    char = "a"
    cp = 0
    for i in range(0, 0x10FFFF):
        try:
            char = chr(i)
            cp = i
        except ValueError:
            # Some code points in the range are not valid Unicode characters
            pass
    return char, cp


# insert_unicode_tuples()
print(get_max_codepoint())
