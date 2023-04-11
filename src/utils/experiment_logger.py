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
        equivalent_collation TEXT NOT NULL,
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
    INSERT INTO
    benchmarks (
        collation,
        equivalent_collation,
        data_table,
        order_by_asc,
        order_by_desc,
        equals
    )
    VALUES
    (
        :collation,
        :equivalent_collation,
        :data_table,
        :order_by_asc,
        :order_by_desc,
        :equals
    );
    """
    db.execute(statement, result)
    db.commit()
    log.debug(f"Logged benchmark result: {result}")


def get_results():
    """Report on all experiment results (aggregated)."""
    db = sqlite3.connect(DATABASE_FILE)
    query = """
    -- sql
    SELECT
        collation,
        equivalent_collation,
        data_table,
        ROUND(AVG(order_by_asc), 3) AS order_by_asc,
        ROUND(AVG(order_by_desc), 3) AS order_by_desc,
        ROUND(AVG(equals), 3) AS equals,
        COUNT(*) AS count
    FROM
        benchmarks
    GROUP BY
        collation,
        equivalent_collation,
        data_table;
    """
    return db.execute(query).fetchall()


def get_comparison():
    """
    Report on experiment results for ICU collations, showing relative
    slowdown compared to equivalent MySQL collations.
    """
    db = sqlite3.connect(DATABASE_FILE)
    query = """
    -- sql
    WITH cte AS (
    SELECT
        collation,
        equivalent_collation,
        data_table,
        ROUND(AVG(order_by_asc), 3) AS order_by_asc,
        ROUND(AVG(order_by_desc), 3) AS order_by_desc,
        ROUND(AVG(equals), 3) AS equals,
        COUNT(*) AS count
    FROM
        benchmarks
    GROUP BY
        collation,
        equivalent_collation,
        data_table
    )
    SELECT
        cte1.collation,
        cte1.equivalent_collation,
        cte1.data_table,
        ROUND(
            100.0 * (cte1.order_by_asc - cte2.order_by_asc) / cte2.order_by_asc,
            2
        ) AS order_by_asc_slowdown,
        ROUND(
            100.0 * (cte1.order_by_desc - cte2.order_by_desc) / cte2.order_by_desc,
            2
        ) AS order_by_desc_slowdown,
        ROUND(
            100.0 * (cte1.equals - cte2.equals) / cte2.equals,
            2
        ) AS equals_slowdown
    FROM
        cte AS cte1
    JOIN cte AS cte2 ON cte1.collation = cte2.equivalent_collation
    AND cte1.data_table = cte2.data_table
    WHERE
        cte1.collation LIKE '%icu%'
    ORDER BY
        cte1.collation,
        cte1.data_table;
    """
    return db.execute(query).fetchall()


if __name__ == "__main__":
    log.setLevel(logging.DEBUG)
    init()
