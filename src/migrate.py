import click
import logging
import inspect
import os
import unicodedata
import re
from datetime import datetime
from utils.custom_logger import log
from db import Connector
from pathlib import Path

TABLE = "migrations"


def get_migration_folder():
    """Get the full path to the migrations folder."""
    root = Path(__file__).parent.parent
    migrations_folder = os.path.join(root, "migrations")

    if not os.path.exists(migrations_folder):
        log.error(f"Could not find migrations folder at {migrations_folder}")
        raise Exception(f"Migrations folder does not exist: {migrations_folder}")

    return migrations_folder


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
def init():
    """Set up migrations table."""
    log.debug("Initializing database...")
    conn = Connector()

    migrations_folder = get_migration_folder()
    log.debug(f"Migrations folder is {migrations_folder}")

    # Create migrations table
    statement = f"""
    -- sql
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename TEXT NOT NULL,
        applied_at DATETIME NOT NULL
    );
    """
    conn.cursor.execute(statement)
    conn.connection.commit()
    conn.close()
    log.debug("Migrations table is initialized.")

    log.info("Migration system is ready to use.")


def slugify(value, allow_unicode=False):
    """
    Converts a string into a valid slug which can be used in URLs and filenames.

    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


@cli.command()
@click.option(
    "-d",
    "--description",
    type=str,
    required=True,
    prompt="Add a description for the migration",
    help="Description of migration, e.g. 'Add examples table'.",
)
def make(description: str):
    """Create a new migration file from the CLI."""
    make_migration(description=description)


def make_migration(description: str, sql=None):
    """Create a new migration file."""

    log.debug("Creating new migration file...")

    # Use current timestamp as prefix, formatted as YYYY-MM-DD-HHMMSS
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(f"{timestamp}_{description}")
    filename = f"{slug}.sql"

    template = f"""
    -- {description}

    BEGIN;

    {sql if sql is not None else "-- TODO: Write migration code here"}

    COMMIT;
    """
    # Clean up identation and remove leading whitespace
    output = inspect.cleandoc(template)

    # Create new migration file in migrations folder
    migrations_folder = get_migration_folder()
    path = os.path.join(migrations_folder, filename)
    with open(path, "w") as f:
        f.write(output)

    log.info(f"Successfully created migration file: {path}")
    log.info("Add your migration code to the file and run 'migrate.py up' to apply it.")


@cli.command()
def up():
    """Run all migrations."""
    # Find all .sql files in the migration folder
    migrations_folder = get_migration_folder()
    migrations = [m for m in os.listdir(migrations_folder) if m.endswith(".sql")]

    total_migration_count = len(migrations)
    applied_migration_count = 0

    # Sort them by timestamp (i.e. filename)
    migrations.sort()

    # Get a list of already applied migrations
    conn = Connector()
    conn.cursor.execute(f"SELECT filename FROM {TABLE};")
    applied_migrations = conn.cursor.fetchall()
    applied_migrations = [m[0] for m in applied_migrations]

    # For each file, check if it has already been applied

    for migration in migrations:
        if migration in applied_migrations:
            log.debug(f"Migration has already been applied: {migration}")
            continue

        log.info(f"Applying migration: {migration}")
        path = os.path.join(migrations_folder, migration)
        conn.execute_script(path)
        applied_migration_count += 1

        # Update the migrations table
        conn.cursor.execute(
            f"INSERT INTO {TABLE} (filename, applied_at) VALUES (%s, %s);",
            (migration, datetime.now()),
        )
        conn.connection.commit()

    log.info(f"New migrations applied: {applied_migration_count}")
    log.info(f"Total migrations applied: {total_migration_count}")


if __name__ == "__main__":
    cli()
