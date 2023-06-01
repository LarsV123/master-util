from utils.custom_logger import log
from db import Connector
from utils.profile import get_runtime
from benchmarks import COLLATIONS

"""
Util functions for performance testing with perf.
"""


def get_data_table(locale: str):
    """
    Return the name of the data table for a given collation.
    """
    if locale == "en_US":
        return "test_en_US_1000000"
    elif locale == "nb_NO":
        return "test_nb_NO_1000000"
    elif locale == "fr_FR":
        return "test_fr_FR_1000000"
    elif locale == "zh_Hans":
        return "test_zh_Hans_1000000"
    elif locale == "ja_JP":
        return "test_ja_JP_1000000"
    else:
        raise ValueError(f"Unknown locale: {locale}")


def load_test(collation: str, iterations: int, locale: str):
    """
    Run a simplified performance benchmark, checking execution time for an
    ORDER BY query against a single table.
    This can be used to generate data for perf.
    """
    log.info("Running load test with ORDER BY query")
    conn = Connector()
    table = get_data_table(locale)
    log.info(f"Table: {table} | Collation: {collation}")

    query = f"""
    -- sql
    SELECT * FROM {table}
    ORDER BY value COLLATE {collation}
    LIMIT 1;
    """

    @get_runtime
    def timed_query():
        conn.cursor.execute(query)

    log.info(
        f"Running {iterations} iterations of the same ORDER_BY query on collation {collation}"
    )
    for _ in range(iterations):
        runtime = timed_query()
        log.info(f"Query took {runtime:.2f} seconds")
        conn.cursor.fetchall()
