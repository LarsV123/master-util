"""
Utility for logging experiment results to an SQLite database.
SQLite is used for logging instead of the running MySQL server,
to avoid conflict with running benchmarks.
"""
import sqlite3
import logging

from utils.custom_logger import log

DATABASE_FILE = "experiments.db"


def reset(conn: sqlite3.Connection):
    """Reset the database to a clean state."""
    log.debug("Resetting database...")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS benchmarks;")
    conn.commit()


def init():
    """Set up log table."""
    db = sqlite3.connect(DATABASE_FILE)
    reset(db)

    log.debug("Initializing database...")

    """
    Create a table which holds the results of testing a single collation once
    """
    statement = """
    -- sql
    CREATE TABLE IF NOT EXISTS benchmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collation TEXT NOT NULL,
        data_table TEXT NOT NULL,
        order_by_asc REAL NOT NULL,
        order_by_desc REAL NOT NULL,
        equals REAL NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    db.execute(statement)
    db.commit()
    log.debug("Database initialized.")


def log_benchmark(result: dict):
    """Log an experiment result to the database."""
    db = sqlite3.connect(DATABASE_FILE)
    statement = """
    -- sql
    INSERT INTO benchmarks (collation, data_table, order_by_asc, order_by_desc, equals)
    VALUES (:collation, :data_table, :order_by_asc, :order_by_desc, :equals);
    """
    db.execute(statement, result)
    db.commit()
    log.debug(f"Logged benchmark result: {result}")


def get_results():
    """Report on experiment results."""
    db = sqlite3.connect(DATABASE_FILE)
    query = """
    -- sql
    SELECT
        collation,
        data_table,
        ROUND(AVG(order_by_asc), 3),
        ROUND(AVG(order_by_desc), 3),
        ROUND(AVG(equals), 3),
        COUNT(*) AS count
    FROM
        benchmarks
    GROUP BY
        collation,
        data_table;
    """
    return db.execute(query).fetchall()


if __name__ == "__main__":
    log.setLevel(logging.DEBUG)
    init()
