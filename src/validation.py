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
    # Get test data
    strings = get_test_data(connection1, collation1)

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
    pbar = tqdm(total=len(strings) - 1)

    for i in range(1, len(strings)):
        s1 = strings[i - 1]
        s2 = strings[i]

        connection1.cursor.execute(query1, (s1, s2, s1, s2))
        result1 = connection1.cursor.fetchone()

        connection2.cursor.execute(query2, (s1, s2, s1, s2))
        result2 = connection2.cursor.fetchone()

        less_than_or_equal = result2[0] or result2[1]
        if not less_than_or_equal:
            pbar.close()
            log.warning("The collations do not place the strings in the same order.")
            log.info(f"String 1: {s1=} | {[hex(ord(c)) for c in s1]}")
            log.info(f"String 2: {s2=} | {[hex(ord(c)) for c in s2]}")
            log.info(f"{collation1}: equal={result1[0]} | less_than={result1[1]}")
            log.info(f"{collation2}: equal={result2[0]} | less_than={result2[1]}")
            return False

        if result1 != result2:
            pbar.close()
            log.warning("The collations do not agree on the comparison result.")
            log.info(f"String 1: {s1=} | {[hex(ord(c)) for c in s1]}")
            log.info(f"String 2: {s2=} | {[hex(ord(c)) for c in s2]}")
            log.info(f"{collation1}: equal={result1[0]} | less_than={result1[1]}")
            log.info(f"{collation2}: equal={result2[0]} | less_than={result2[1]}")
            return False

        pbar.update(1)

    return True


# This is unfinished, disable linter warnings for now
# flake8: noqa
# mypy: ignore-errors
def find_collation_differences(
    connection1: Connector, connection2: Connector, collation1: str, collation2: str
) -> list:
    """
    Find all differences between two collations.
    This is a brute-force approach that compares all possible combinations of
    characters in the Unicode range, as well as a set of test strings.
    It is very slow and should only be used after the `validate_collations`
    function has determined that a difference exists.

    It assumes that connection1 and collation1 are the reference implementation,
    i.e. "correct", and will compare connection2 and collation2 to that.
    """
    log.debug("Getting test data...")
    strings = get_test_data(connection1, collation1)
    total_size = len(strings)
    total_comparisons = total_size * total_size / 2

    log.debug("Comparing strings...")
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

    differences = []

    # Naive implementation, no optimizations
    for i in range(0, total_size):
        s1 = strings[i]
        for j in range(i, total_size):
            s2 = strings[j]
            connection1.cursor.execute(query1, (s1, s2, s1, s2))
            result1 = (
                connection1.cursor.fetchone()
            )  # Tuple on the form (equal, less_than)

            connection2.cursor.execute(query2, (s1, s2, s1, s2))
            result2 = (
                connection2.cursor.fetchone()
            )  # Tuple on the form (equal, less_than)

            if result1 != result2:
                differences.append((s1, s2, result1, result2))

    # Compare all characters against each other in batches
    batch_size = 1000
    # TODO: Implement this function
    pass


def get_test_data(connection: Connector, collation: str) -> list[str]:
    """
    Retrieve the list of test strings from the database, ordered by the given
    collation.
    """
    tables = ["sample_strings", "unicode_characters"]
    for t in tables:
        log.debug(f"Counting rows in {t}...")
        connection.cursor.execute(f"SELECT COUNT(*) FROM {t};")
        count = connection.cursor.fetchone()[0]
        log.debug(f"{t} contains {count} rows.")
        assert count > 0

    log.debug("Fetching test strings from the database...")
    query = f"""
    -- sql
    SELECT s FROM (
        SELECT string AS s FROM sample_strings
        UNION
        SELECT char_value AS s FROM unicode_characters
    ) AS t
    ORDER BY t.s COLLATE {collation} ASC;
    """
    connection.cursor.execute(query)
    strings = [s[0] for s in connection.cursor.fetchall()]
    log.debug(f"Fetched {len(strings)} strings from the database.")
    assert len(strings) > 0
    return strings
