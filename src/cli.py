import click
import logging
from utils.custom_logger import log
from db import Connector
from utils.initialize import prepare_performance_benchmarks, prepare_validity_tests
from benchmarks import performance_benchmark, print_results
import utils.experiment_logger as experiment_logger
from experiment2 import load_test
from validation import validate_collations


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging.")
@click.option("-q", "--quiet", is_flag=True, help="Disable non-error logging.")
def cli(verbose: bool, quiet: bool):
    if quiet:
        log.setLevel(logging.ERROR)
    elif verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    pass


@cli.command()
def test():
    """Test the logger and the database connection."""
    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning")
    log.error("This is an error")
    conn = Connector()
    conn.close()
    log.info("Successfully connected to database.")


@cli.command()
@click.option("-c", "--collation", default="utf8mb4_icu_en_US_ai_ci")
@click.option("-i", "--iterations", default=3, help="Number of times to run the test.")
@click.option(
    "-t", "--test-all", is_flag=True, help="Run a set of tests on various collations."
)
@click.option(
    "-l", "--locale", default="en_US", help="Locale to use for the test data."
)
def stresstest(collation: str, iterations: int, test_all: bool, locale: str):
    """Run benchmarks using ICU collation, to produce data for perf."""
    if test_all:
        collations = [
            "utf8mb4_icu_en_US_ai_ci",
            "utf8mb4_icu_en_US_as_cs",
            "utf8mb4_icu_nb_NO_ai_ci",
            "utf8mb4_icu_fr_FR_ai_ci",
            "utf8mb4_icu_zh_Hans_as_cs",
            "utf8mb4_icu_ja_JP_as_cs",
            "utf8mb4_icu_ja_JP_as_cs_ks",
            "utf8mb4_0900_ai_ci",
            "utf8mb4_0900_as_cs",
            "utf8mb4_nb_0900_ai_ci",
            "utf8mb4_zh_0900_as_cs",
            "utf8mb4_ja_0900_as_cs",
            "utf8mb4_ja_0900_as_cs_ks",
        ]
        for c in collations:
            load_test(c, iterations, locale)
    else:
        load_test(collation, iterations, locale)


@cli.command()
@click.option("-p", "--perf", default=True, help="Initialize performance benchmarks.")
@click.option("-v", "--valid", default=True, help="Initialize validity tests.")
def init(perf: bool, valid: bool):
    """Set up tables with required test data for all experiments."""
    log.info("Initializing database...")

    log.debug(f"Initializing performance benchmarks: {perf}")
    if perf:
        prepare_performance_benchmarks()

    log.debug(f"Initializing validity tests: {valid}")
    if valid:
        prepare_validity_tests()


@cli.command()
@click.option("-i", "--iterations", default=3, help="Number of times to run the test.")
@click.option(
    "-r",
    "--reset",
    is_flag=True,
    help="Reset the log database before running the test.",
)
@click.option(
    "-m", "--mysql", is_flag=True, help="Include MySQL collations in the benchmark."
)
def perf(iterations: int, reset: bool, mysql: bool):
    """
    Runs a set of performance benchmarks.
    Results are logged to an SQLite database.
    """
    if reset:
        log.info("Resetting the log database...")
        experiment_logger.reset()
    log.info("Running performance benchmarks...")

    # Prompt user for ICU_FROZEN boolean
    ICU_FROZEN = click.prompt(
        "What is the value of ICU_FROZEN? (true/false)", type=bool, default="false"
    )

    # Prompt user for ICU_EXTRA TAILORING boolean
    ICU_EXTRA_TAILORING = click.prompt(
        "What is the value of ICU_EXTRA_TAILORING? (true/false)",
        type=bool,
        default="false",
    )

    performance_benchmark(
        iterations, ICU_FROZEN, ICU_EXTRA_TAILORING, include_mysql=mysql
    )


@cli.command()
def report():
    """Report results from performance benchmarks."""
    print_results()


@cli.command()
@click.option(
    "-p1", "--port1", default=3306, help="Port number for the first connection."
)
@click.option(
    "-p2", "--port2", required=True, help="Port number for the second connection."
)
@click.option(
    "-c1", "--collation1", required=True, help="Collation for the first connection."
)
@click.option(
    "-c2", "--collation2", required=True, help="Collation for the second connection."
)
def validate(port1: int, port2: int, collation1: str, collation2: str):
    """
    Run a simplified validity test, which is intended to check if two collations
    produce identical results. This runs a set of queries against two
    separate connections, and compares the results.

    Use the same port for both connections if you want to test different collations
    from the same MySQL build.
    """
    log.info("Running validity tests...")
    log.info(f"Port 1: {port1} | Collation 1: {collation1}")
    log.info(f"Port 2: {port2} | Collation 2: {collation2}")

    connection1 = Connector(port=port1)
    connection2 = Connector(port=port2)
    success = validate_collations(connection1, connection2, collation1, collation2)

    connection1.close()
    connection2.close()
    log.info(f"Validity test success: {success}")
    if success:
        log.info("The collations are equivalent.")
    else:
        log.info("The collations are not equivalent.")


if __name__ == "__main__":
    cli()
