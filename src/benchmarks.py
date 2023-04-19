import locale
from db import Connector
from utils.custom_logger import log
from utils.profile import get_runtime
from utils import experiment_logger
from tabulate import tabulate
from tqdm import tqdm


# This is used to format numbers with thousands separators (e.g. 123 456 780).
locale.setlocale(locale.LC_ALL, "")


# All combinations of locale and collation we want to test
COLLATIONS = [
    {
        "icu": "utf8mb4_icu_en_US_ai_ci",
        "mysql": "utf8mb4_0900_ai_ci",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_en_US_as_cs",
        "mysql": "utf8mb4_0900_as_cs",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_nb_NO_ai_ci",
        "mysql": "utf8mb4_nb_0900_ai_ci",
        "locale": "nb_NO",
    },
    {
        "icu": "utf8mb4_icu_nb_NO_ai_ci",
        "mysql": "utf8mb4_nb_0900_ai_ci",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_fr_FR_ai_ci",
        "mysql": "utf8mb4_0900_ai_ci",
        "locale": "fr_FR",
    },
    {
        "icu": "utf8mb4_icu_fr_FR_ai_ci",
        "mysql": "utf8mb4_0900_ai_ci",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_zh_Hans_as_cs",
        "mysql": "utf8mb4_zh_0900_as_cs",
        "locale": "zh_Hans",
    },
    {
        "icu": "utf8mb4_icu_zh_Hans_as_cs",
        "mysql": "utf8mb4_zh_0900_as_cs",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_ja_JP_as_cs",
        "mysql": "utf8mb4_ja_0900_as_cs",
        "locale": "ja_JP",
    },
    {
        "icu": "utf8mb4_icu_ja_JP_as_cs",
        "mysql": "utf8mb4_ja_0900_as_cs",
        "locale": "en_US",
    },
    {
        "icu": "utf8mb4_icu_ja_JP_as_cs_ks",
        "mysql": "utf8mb4_ja_0900_as_cs_ks",
        "locale": "ja_JP",
    },
    {
        "icu": "utf8mb4_icu_ja_JP_as_cs_ks",
        "mysql": "utf8mb4_ja_0900_as_cs_ks",
        "locale": "en_US",
    },
]

# The sizes of dataset we actually test
DATASET_SIZES = [100000, 1000000, 10000000]


def performance_benchmark(iterations: int, tailoring_size: int):
    """
    Run a performance benchmark comparing different collations.
    Each configuration is run `iterations + 1` times, where the first
    is a "warm-up" run which is not logged.

    The `tailoring_size` parameter refers to the number of tailoring rules
    added to the collation when compiling MySQL.
    """
    conn = Connector()
    pre_check(conn)
    experiment_logger.init()

    # Generate all combinations of collations, locales and dataset sizes
    configurations = []

    # We only need to benchmark each collation once per locale
    done: dict[str, list[str]] = {collation["locale"]: [] for collation in COLLATIONS}

    for collation in COLLATIONS:
        locale = collation["locale"]
        if collation["icu"] not in done[locale]:
            for size in DATASET_SIZES:
                configurations.append(
                    {
                        "collation": collation["icu"],
                        "locale": locale,
                        "data_table": f"test_{locale}_{size}",
                        "data_size": size,
                        "tailoring_size": tailoring_size,
                    }
                )
            done[locale].append(collation["icu"])

        if collation["mysql"] not in done[locale]:
            for size in DATASET_SIZES:
                configurations.append(
                    {
                        "collation": collation["mysql"],
                        "locale": locale,
                        "data_table": f"test_{locale}_{size}",
                        "data_size": size,
                        "tailoring_size": tailoring_size,
                    }
                )
            done[locale].append(collation["mysql"])

    tqdm.write("Running performance benchmarks...")
    tqdm.write(f"Number of configurations: {len(configurations)}")
    steps = len(configurations) * (iterations + 1)
    pbar = tqdm(total=steps)
    completed = 0
    for config in configurations:
        # Warm-up run
        status = f"{config['collation']} (0/{iterations})"
        pbar.set_description(status)
        test_collation(conn, config)
        pbar.update(1)

        for i in range(iterations):
            status = f"{config['collation']} ({i+1}/{iterations})"
            pbar.set_description(status)
            result = test_collation(conn, config)
            experiment_logger.log_benchmark(result)
            pbar.update(1)
        completed += 1
        tqdm.write(f"Completed {completed}/{len(configurations)} configurations")

    pbar.close()
    conn.close()
    report_results()


def report_results():
    """Print the results of the performance benchmark."""
    print("All results (aggregated):")
    print("*" * 80)
    print(
        tabulate(
            experiment_logger.get_results(),
            headers=[
                "Collation",
                "Data set",
                "Data size",
                "Tailoring size",
                "Order by (ASC)",
                "Order by (DESC)",
                "Equals",
                "Iterations",
            ],
            tablefmt="mysql",
        )
    )
    print("*" * 80)

    print("Relative slowdown (ICU vs MySQL):")
    results = []
    for config in COLLATIONS:
        results.extend(experiment_logger.get_comparison(config))
    print("*" * 80)
    print(
        tabulate(
            results,
            headers=[
                "ICU collation",
                "MySQL collation",
                "Locale",
                "Data size",
                "Tailoring size",
                "ASC slowdown (%)",
                "DESC slowdown (%)",
                "Equals slowdown (%)",
            ],
            tablefmt="mysql",
        )
    )
    print("*" * 80)


def test_collation(conn: Connector, config: dict):
    """Run all performance benchmarks for a given collation."""
    log.debug(f"Testing collation: {config['collation']}")
    result = config

    result["order_by_asc"] = benchmark_order_by(
        conn, config["data_table"], config["collation"], ascending=True
    )

    result["order_by_desc"] = benchmark_order_by(
        conn, config["data_table"], config["collation"], ascending=False
    )

    result["equals"] = benchmark_equals(
        conn,
        config["data_table"],
        config["collation"],
    )
    return result


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
