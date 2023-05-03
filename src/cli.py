import click
import logging
from utils.custom_logger import log
from db import Connector
from test_data_handler import (
    insert_all_locale_data,
    create_test_tables,
)
from benchmarks import performance_benchmark, report_results
import utils.experiment_logger as experiment_logger
from perf_utils import perf_load_test
from validation import reset_validity_tables, validate_collations


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
def init():
    """
    Set up tables with test data for all locales.
    This is based on the country-list repo.
    This should only be run once.
    """
    log.debug("Inserting test data for all locales...")
    insert_all_locale_data()
    # TODO: Add a reset method so we can re-run this and start with clean tables.
    # TODO: Add extra tables with synthetic data for testing (e.g. cross-join the current data)


@cli.command()
def setup_perf():
    """Set up synthetic data for a quick test"""
    log.info("Creating synthetic test data...")
    create_test_tables()
    log.info("Finished creating synthetic test data.")


@cli.command()
@click.option("-i", "--iterations", default=3, help="Number of times to run the test.")
@click.option(
    "-d",
    "--delta",
    required=True,
    help="Number of tailoring rules added to the ICU collations as a prefix.",
)
@click.option(
    "-r",
    "--reset",
    is_flag=True,
    help="Reset the log database before running the test.",
)
def perf(iterations: int, delta: int, reset: bool):
    """
    Runs a set of performance benchmarks.
    Results are logged to an SQLite database.
    """
    if reset:
        log.info("Resetting the log database...")
        experiment_logger.reset()
    log.info("Running performance benchmarks...")
    log.info("Running a simplified set of performance benchmarks...")
    performance_benchmark(iterations, delta)


@cli.command()
def report():
    """Report results from performance benchmarks."""
    report_results()


@cli.command()
@click.option("-c", "--collation", default="utf8mb4_icu_en_US_ai_ci")
def stresstest(collation: str):
    """Run benchmarks using ICU collation, to produce data for perf."""
    perf_load_test(collation)


@cli.command()
@click.option(
    "-r",
    "--reset",
    is_flag=True,
    help="Truncate and reinsert the character table before running the test.",
)
def validate(reset: bool):
    """Run a simplified validity test"""
    log.info("Running validity tests...")
    collation1 = "utf8mb4_icu_nb_NO_ai_ci"
    collation2 = "utf8mb4_icu_nb_NO_ai_ci"
    # c2 = "utf8mb4_icu_en_US_ai_ci"
    # c2 = "utf8mb4_nb_0900_ai_ci"

    log.info(f"Collation 1: {collation1}")
    log.info(f"Collation 2: {collation2}")
    connection1 = Connector()
    connection2 = Connector()
    if reset:
        reset_validity_tables(connection1)
    validate_collations(connection1, connection2, collation1, collation2)

    connection1.close()
    connection2.close()


if __name__ == "__main__":
    cli()
