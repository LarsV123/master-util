import locale
from db import Connector
from utils.custom_logger import log
from utils.profile import get_runtime
from utils import experiment_logger
from utils.initialize import DATASET_SIZES
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


def performance_benchmark(
    iterations: int, ICU_FROZEN: bool, ICU_EXTRA_TAILORING: bool, include_mysql: bool
):
    """
    Run a performance benchmark comparing different collations.
    Each configuration is run `iterations + 1` times, where the first
    is a "warm-up" run which is not logged.

    If the `include_mysql` flag is set, the benchmark will also run
    the same tests using the nearest equivalent MySQL collations.
    """
    conn = Connector()
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
                        "ICU_FROZEN": ICU_FROZEN,
                        "ICU_EXTRA_TAILORING": ICU_EXTRA_TAILORING,
                    }
                )
            done[locale].append(collation["icu"])

        if include_mysql and collation["mysql"] not in done[locale]:
            for size in DATASET_SIZES:
                configurations.append(
                    {
                        "collation": collation["mysql"],
                        "locale": locale,
                        "data_table": f"test_{locale}_{size}",
                        "data_size": size,
                        "ICU_FROZEN": ICU_FROZEN,
                        "ICU_EXTRA_TAILORING": ICU_EXTRA_TAILORING,
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

    total_results = experiment_logger.count_results()
    log.info(f"Total number of results logged: {total_results}")


def print_results():
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
                "ICU_FROZEN",
                "ICU_EXTRA_TAILORING",
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
                "ICU_FROZEN",
                "ICU_EXTRA_TAILORING",
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


def benchmark_order_by(db: Connector, table: str, collation: str, ascending: bool):
    direction = "ASC" if ascending else "DESC"
    query = f"""
    -- sql
    SELECT * FROM {table}
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
    SELECT * FROM {table}
    WHERE value = 'Norge123' COLLATE {collation};
    """
    log.debug(f"{query=}")

    @get_runtime
    def timed_equals():
        db.cursor.execute(query)

    runtime = timed_equals()
    db.cursor.fetchall()
    return runtime
