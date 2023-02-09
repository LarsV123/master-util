import click
import logging
from utils.custom_logger import log
from db import Connector
from test_data_handler import insert_all_locale_data


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


if __name__ == "__main__":
    cli()
