import locale
from db import Connector
from utils.custom_logger import log
from utils.profile import get_runtime
from utils import experiment_logger
from tabulate import tabulate
from tqdm import tqdm

# This is used to format numbers with thousands separators (e.g. 123 456 780).
locale.setlocale(locale.LC_ALL, "")

# Pairs of collations which should be equivalent
COLLATIONS = [
    ("utf8mb4_nb_icu_ai_ci", "utf8mb4_nb_0900_ai_ci"),
    ("utf8mb4_us_icu_ai_ci", "utf8mb4_0900_ai_ci"),
    ("utf8mb4_us_icu_as_cs", "utf8mb4_0900_as_cs"),
    ("utf8mb4_fr_icu_ai_ci", "utf8mb4_0900_ai_ci"),
    ("utf8mb4_zh_icu_0900_as_cs", "utf8mb4_zh_0900_as_cs"),
    ("utf8mb4_ja_icu_0900_as_cs", "utf8mb4_ja_0900_as_cs"),
    ("utf8mb4_ja_icu_0900_as_cs_ks", "utf8mb4_ja_0900_as_cs_ks"),
]


def performance_benchmark():
    """Run a performance benchmark comparing different collations."""
    conn = Connector()
    pre_check(conn)

    loops = 3
    table = "test1_no_NO"

    # Find all collations to test
    collations = []
    for c1, c2 in COLLATIONS:
        collations.append(c1)
        collations.append(c2)
    collations = list(set(collations))  # Remove duplicates, keep order

    steps = len(COLLATIONS) * 3 * 2
    pbar = tqdm(steps)

    experiment_logger.init()

    for _ in range(loops):
        for collation in collations:
            test_collation(conn, table, collation, pbar)

    pbar.close()
    conn.close()
    print("*" * 80)
    results = experiment_logger.get_results()
    print(
        tabulate(
            results,
            headers=[
                "Collation",
                "Table",
                "Avg. order_by_asc",
                "Avg. order_by_desc",
                "Avg. equals",
                "Iterations",
            ],
            tablefmt="mysql",
        )
    )


def test_collation(conn: Connector, table: str, collation: str, pbar: tqdm):
    """Run all performance benchmarks for a given collation."""
    log.debug(f"Testing collation: {collation}")
    tqdm.write(f"Testing collation: {collation}")
    result = {"collation": collation, "data_table": table}

    pbar.set_description("order_by_asc")
    result["order_by_asc"] = benchmark_order_by(conn, table, collation, ascending=True)
    pbar.update(1)

    pbar.set_description("order_by_desc")
    result["order_by_desc"] = benchmark_order_by(
        conn, table, collation, ascending=False
    )
    pbar.update(1)

    pbar.set_description("equals")
    result["equals"] = benchmark_equals(conn, table, collation)
    pbar.update(1)

    tqdm.write(f"Done testing {collation}")
    experiment_logger.log_benchmark(result)


def validity_tests():
    """Check that pairs of collations produce the same results."""
    conn = Connector()
    pre_check(conn)

    table = "country_list_no_NO"
    collations = [
        ("utf8mb4_nb_icu_ai_ci", "utf8mb4_nb_0900_ai_ci"),
        ("utf8mb4_us_icu_ai_ci", "utf8mb4_0900_ai_ci"),
        ("utf8mb4_0900_ai_ci", "utf8mb4_nb_0900_ai_ci"),
        ("utf8mb4_us_icu_ai_ci", "utf8mb4_nb_icu_ai_ci"),
    ]
    results = []

    pbar = tqdm(collations)
    for c1, c2 in pbar:
        tqdm.write(f"Comparing {c1} and {c2} (ascending)...")
        result = compare_collations(conn, table, c1, c2)
        tqdm.write(f"Found {result} differences.")
        results.append(
            {
                "c1": c1,
                "c2": c2,
                "differences": result,
            }
        )

    pbar.close()
    conn.close()
    print("*" * 80)
    print(tabulate(results, headers="keys", tablefmt="mysql"))


def compare_collations(db: Connector, table: str, c1: str, c2: str):
    """Compare two collations. Return the number of rows that are different."""
    r1 = get_order_by(db, table, c1, ascending=False)
    r2 = get_order_by(db, table, c2, ascending=False)

    differences = 0
    assert len(r1) == len(r2)
    for i in range(len(r1)):
        if r1[i] != r2[i]:
            log.debug(f"Row {i} is different: {r1[i]} != {r2[i]}")
            differences += 1
    return differences


def get_order_by(db: Connector, table: str, collation: str, ascending: bool):
    direction = "ASC" if ascending else "DESC"
    query = f"""
    -- sql
    SELECT * FROM my_project.{table}
    ORDER BY value COLLATE {collation}
    {direction};
    """
    db.cursor.execute(query)
    return db.cursor.fetchall()


def pre_check(db: Connector):
    """Check that the tables exist."""
    query = "SELECT COUNT(*), MIN(VALUE), MAX(value) FROM my_project.test1_no_NO;"
    db.cursor.execute(query)
    count, min_value, max_value = db.cursor.fetchone()
    log.info(f"Table test1_no_NO has {count:n} rows. {min_value=}, {max_value=}")


def benchmark_order_by(db: Connector, table: str, collation: str, ascending: bool):
    direction = "ASC" if ascending else "DESC"
    query = f"""
    -- sql
    SELECT * FROM my_project.{table}
    ORDER BY value COLLATE {collation}
    {direction} LIMIT 1;
    """
    log.debug(f"{query=}")
    log.debug(f"{ascending=}")

    @get_runtime
    def timed_order_by():
        db.cursor.execute(query)

    runtime = timed_order_by()
    db.cursor.fetchall()
    return runtime


def benchmark_equals(db: Connector, table: str, collation: str):
    query = f"""
    SELECT * FROM my_project.{table}
    WHERE value = 'Norge123' COLLATE {collation};
    """
    log.debug(f"{query=}")

    @get_runtime
    def timed_equals():
        db.cursor.execute(query)

    runtime = timed_equals()
    db.cursor.fetchall()
    return runtime
