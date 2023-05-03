# Tools for validating that two collations produce the same results.

from tqdm import tqdm
from db import Connector
from utils.custom_logger import log


def validate_collations(
    connection1: Connector,
    connection2: Connector,
    collation1: str,
    collation2: str,
) -> bool:
    """
    Verify that two collations are equivalent.
    Returns True if the collations are equivalent, otherwise False.

    Accepts two database connections as parameters, to support comparing
    collations in different databases, but these can be connections to the same
    database. Connection1 is the "primary" connection and is assumed to be a
    connection to a database with the test tables already created and filled.

    Two collations are considered equivalent if they would produce the same
    total ordering for all strings. This is checked by first ordering a list of
    test strings and all valid Unicode characters by the first collation in
    ascending order, and then comparing pairs of elements in that list using
    both collations.

    Equal strings are not guaranteed to be in any particular order when sorting,
    but they must be adjacent to each other in the sorted list. This means that
    the result of comparing adjacent strings to each other should be the same
    for both collations.

    If the two collations are equivalent, the result of the comparison should
    be the same for every pair.
    Also, if the second collation is equivalent to the first, the second element
    in the pair should always be greater than or equal to the first element.

    Examples:
    c1 = [a = A < b = B < c = C]
    c2 = [a < A < b < B < c < C]
    Not equivalent. This is caught by the first check.

    c1 = [a = A < b = B < c = C]
    c2 = [b = B < a = A < c = C]
    Not equivalent. This is caught by the second check.

    c1 = [a = A < b = B < c = C]
    c2 = [A = a < B = b < C = c]
    Equivalent. This should pass all checks.
    """
    log.debug(f"Validating collations {collation1=} and {collation2=}...")

    # Get count of characters in test tables
    """
    test_strings: This contains arbitrary strings used for testing,
    including all 2-character permutations of the Latin alphabet.

    unicode_characters: This contains all valid Unicode characters.
    """
    tables = ["test_strings", "unicode_characters"]
    for t in tables:
        log.debug(f"Counting rows in {t}...")
        connection1.cursor.execute(f"SELECT COUNT(*) FROM {t};")
        count = connection1.cursor.fetchone()[0]
        log.debug(f"{t} contains {count} rows.")
        assert count > 0

    log.debug("Fetching test strings from the database...")
    query = f"""
    -- sql
    SELECT s FROM (
        SELECT string AS s FROM test_strings
        UNION
        SELECT char_value AS s FROM unicode_characters
    ) AS t
    ORDER BY t.s COLLATE {collation1} ASC;
    """
    connection1.cursor.execute(query)
    strings = connection1.cursor.fetchall()
    log.debug(f"Fetched {len(strings)} strings from the database.")
    assert len(strings) > 0

    log.debug("Comparing adjacent strings...")
    query1 = f"""
    -- sql
    SELECT
        %s = %s COLLATE {collation1} AS equal,
        %s < %s COLLATE {collation1} AS less_than;
    """
    log.debug(f"{query1=}")

    query2 = f"""
    -- sql
    SELECT
        %s = %s COLLATE {collation2} AS equal,
        %s < %s COLLATE {collation2} AS less_than;
    """
    log.debug(f"{query2=}")

    for i in tqdm(range(1, len(strings))):
        s1 = strings[i - 1][0]
        s2 = strings[i][0]

        connection1.cursor.execute(query1, (s1, s2, s1, s2))
        result1 = connection1.cursor.fetchone()

        connection2.cursor.execute(query2, (s1, s2, s1, s2))
        result2 = connection2.cursor.fetchone()

        less_than_or_equal = result2[0] or result2[1]
        if not less_than_or_equal:
            log.warning("The collations do not place the strings in the same order.")
            log.info(f"String 1: {s1=} | {[hex(ord(c)) for c in s1]}")
            log.info(f"String 2: {s2=} | {[hex(ord(c)) for c in s2]}")
            log.info(f"{collation1}: equal={result1[0]} | less_than={result1[1]}")
            log.info(f"{collation2}: equal={result2[0]} | less_than={result2[1]}")
            return False

        if result1 != result2:
            log.warning("The collations do not agree on the comparison result.")
            log.info(f"String 1: {s1=} | {[hex(ord(c)) for c in s1]}")
            log.info(f"String 2: {s2=} | {[hex(ord(c)) for c in s2]}")
            log.info(f"{collation1}: equal={result1[0]} | less_than={result1[1]}")
            log.info(f"{collation2}: equal={result2[0]} | less_than={result2[1]}")
            return False

    return True


def reset_validity_tables(conn: Connector):
    """Reset the tables used for the validity test."""

    # Truncate data tables
    log.info("Truncating tables used for validity tests...")
    conn.cursor.execute("TRUNCATE TABLE test_strings;")
    conn.cursor.execute("TRUNCATE TABLE unicode_characters;")

    # Insert all valid Unicode characters
    unicode = create_unicode_tuples()
    log.info(f"Inserting {len(unicode)} Unicode characters into the database...")
    statement = """
    -- sql
    INSERT INTO unicode_characters (code_point, hex_value, char_value)
    VALUES (%s, %s, %s);
    """
    failures = []
    for i in tqdm(range(0, len(unicode))):
        try:
            conn.cursor.execute(statement, unicode[i])
        except Exception as e:
            log.debug(e)
            failures.append(unicode[i])
    log.info(f"Failed to insert {len(failures)} of {len(unicode)} characters.")

    # Insert test strings (2-character permutations of the Latin alphabet)
    strings = create_test_strings()
    log.info(f"Inserting {len(strings)} test strings into the database...")
    statement = "INSERT INTO test_strings (string) VALUES (%s);"
    for i in tqdm(range(0, len(strings))):
        conn.cursor.execute(statement, (strings[i],))

    conn.connection.commit()
    log.info("Finished resetting validity test tables.")


def create_test_strings() -> list[str]:
    """
    Create a list of additional strings to be used when comparing collations.
    For the purposes of this test, this is just a list of 2-character
    permutations of the Latin alphabet.
    """
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    strings = []
    for i in alphabet:
        for j in alphabet:
            strings.append(i + j)
    return strings


def create_unicode_tuples() -> list[tuple[int, str, str]]:
    """
    Create a list of tuples of all characters in the Unicode range.
    Each tuple is on the form (codepoint, hex value of codepoint, character).
    """
    tuples: list[tuple[int, str, str]] = []

    for i in range(0, 0x10FFFF):
        try:
            char = chr(i)
            tuples.append((i, str(hex(i)), char))
        except ValueError:
            # Some code points in the range are not valid Unicode characters
            pass
    log.info(f"Created {len(tuples)} Unicode characters.")
    return tuples
