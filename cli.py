import click
import logging
from utils.custom_logger import log
from db import Connector


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
    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning")
    log.error("This is an error")
    conn = Connector()
    conn.close()


if __name__ == "__main__":
    cli()
