"""
Utility for logging experiment results to an SQLite database.
SQLite is used for logging instead of the running MySQL server,
to avoid conflict with running benchmarks.
"""
import sqlite3
import logging

from utils.custom_logger import log

DATABASE_FILE = "experiments.db"


def reset():
    """Reset the database to a clean state."""
    log.debug("Resetting database...")
    db = sqlite3.connect(DATABASE_FILE)
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS benchmarks;")
    db.commit()


def init():
    """Set up log table."""
    db = sqlite3.connect(DATABASE_FILE)

    log.debug("Initializing database...")

    """
    Create a table which holds the results of testing a single collation once
    """
    statement = """
    -- sql
    CREATE TABLE IF NOT EXISTS benchmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ICU_FROZEN BOOLEAN NOT NULL,
        ICU_EXTRA_TAILORING BOOLEAN NOT NULL,
        collation TEXT NOT NULL,
        locale TEXT NOT NULL,
        data_table TEXT NOT NULL,
        data_size INTEGER NOT NULL,
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
        ICU_FROZEN,
        ICU_EXTRA_TAILORING,
        collation,
        locale,
        data_table,
        data_size,
        order_by_asc,
        order_by_desc,
        equals
    )
    VALUES
    (
        :ICU_FROZEN,
        :ICU_EXTRA_TAILORING,
        :collation,
        :locale,
        :data_table,
        :data_size,
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
        ICU_FROZEN,
        ICU_EXTRA_TAILORING,
        data_table,
        data_size,
        ROUND(AVG(order_by_asc), 3) AS order_by_asc,
        ROUND(AVG(order_by_desc), 3) AS order_by_desc,
        ROUND(AVG(equals), 3) AS equals,
        COUNT(*) AS count
    FROM
        benchmarks
    GROUP BY
        collation,
        ICU_FROZEN,
        ICU_EXTRA_TAILORING,
        data_table,
        data_size;
    """
    return db.execute(query).fetchall()


def get_comparison(config: dict):
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
        ICU_FROZEN,
        ICU_EXTRA_TAILORING,
        locale,
        data_size,
        ROUND(AVG(order_by_asc), 3) AS order_by_asc,
        ROUND(AVG(order_by_desc), 3) AS order_by_desc,
        ROUND(AVG(equals), 3) AS equals,
        COUNT(*) AS count
    FROM
        benchmarks
    GROUP BY
        collation,
        locale,
        data_size,
        ICU_FROZEN,
        ICU_EXTRA_TAILORING
    )
    SELECT
        cte1.collation AS icu,
        cte2.collation AS mysql,
        cte1.locale,
        cte1.data_size,
        cte1.ICU_FROZEN,
        cte1.ICU_EXTRA_TAILORING,
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
    JOIN cte AS cte2 ON cte1.locale = cte2.locale
    WHERE 1
        AND cte1.collation = :icu
        AND cte2.collation = :mysql
        AND cte1.locale = :locale
        AND cte1.data_size = cte2.data_size
        AND cte1.ICU_FROZEN = cte2.ICU_FROZEN
        AND cte1.ICU_EXTRA_TAILORING = cte2.ICU_EXTRA_TAILORING
    ORDER BY
        cte1.locale,
        cte1.data_size,
        cte1.ICU_FROZEN,
        cte1.ICU_EXTRA_TAILORING;
    """
    return db.execute(query, config).fetchall()


if __name__ == "__main__":
    log.setLevel(logging.DEBUG)
    init()
