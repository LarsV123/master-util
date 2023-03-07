import locale
from db import Connector
from utils.custom_logger import log
from utils.profile import get_runtime
from tabulate import tabulate
from tqdm import tqdm

# This is used to format numbers with thousands separators (e.g. 123 456 780).
locale.setlocale(locale.LC_ALL, "")


def performance_benchmark():
    """Run a performance benchmark comparing different collations."""
    conn = Connector()
    pre_check(conn)

    loops = 3
    table = "test1_no_NO"
    collations = [
        "utf8mb4_nb_icu_ai_ci",
        "utf8mb4_nb_0900_ai_ci",
        "utf8mb4_us_icu_ai_ci",
        "utf8mb4_0900_ai_ci",
    ]

    results = []
    pbar = tqdm(collations)

    for collation in pbar:
        tqdm.write(f"Testing collation: {collation}")
        result = {"collation": collation}

        pbar.set_description("order_by_asc")
        result["order_by_asc"] = benchmark_order_by(
            conn, table, collation, repetitions=loops, ascending=True
        )

        pbar.set_description("order_by_desc")
        result["order_by_desc"] = benchmark_order_by(
            conn, table, collation, repetitions=loops, ascending=False
        )

        pbar.set_description("equals")
        result["equals"] = benchmark_equals(conn, table, collation, repetitions=loops)

        tqdm.write(f"Done testing {collation}")
        results.append(result)

    pbar.close()
    conn.close()
    print("*" * 80)
    print(tabulate(results, headers="keys", tablefmt="mysql"))


def pre_check(db: Connector):
    """Check that the tables exist."""
    query = "SELECT COUNT(*), MIN(VALUE), MAX(value) FROM my_project.test1_no_NO;"
    db.cursor.execute(query)
    count, min_value, max_value = db.cursor.fetchone()
    log.info(f"Table test1_no_NO has {count:n} rows. {min_value=}, {max_value=}")


def benchmark_order_by(
    db: Connector, table: str, collation: str, repetitions=2, ascending=False
):
    direction = "ASC" if ascending else "DESC"
    query = f"""
    SELECT * FROM my_project.{table}
    ORDER BY value COLLATE {collation}
    {direction} LIMIT 1;
    """
    log.debug(f"{query=}")
    log.debug(f"{repetitions=} | {ascending=}")

    @get_runtime
    def timed_order_by():
        for _ in range(repetitions):
            db.cursor.execute(query)
            result = db.cursor.fetchall()
        return result

    return timed_order_by()


def benchmark_equals(db: Connector, table: str, collation: str, repetitions=2):
    query = f"""
    SELECT * FROM my_project.{table}
    WHERE value = 'Norge123' COLLATE {collation};
    """
    log.debug(f"{query=}")
    log.debug(f"{repetitions=}")

    @get_runtime
    def timed_equals():
        for _ in range(repetitions):
            db.cursor.execute(query)
            result = db.cursor.fetchall()
        return result

    return timed_equals()
