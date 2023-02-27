from db import Connector
from utils.custom_logger import log
from utils.profile import time_this
import locale

# This is used to format numbers with thousands separators (e.g. 123 456 780).
locale.setlocale(locale.LC_ALL, "")

repetitions = 2


def sanity_test():
    """Run a simple benchmark comparing the two approaches."""
    conn = Connector()
    pre_check(conn)
    icu_order_by(conn)
    mysql_order_by(conn)
    icu_equals(conn)
    mysql_equals(conn)
    conn.close()


def pre_check(db: Connector):
    """Check that the tables exist."""
    query = "SELECT COUNT(*), MIN(VALUE), MAX(value) FROM my_project.test1_no_NO;"
    db.cursor.execute(query)
    count, min_value, max_value = db.cursor.fetchone()
    log.info(f"Table test1_no_NO has {count:n} rows. {min_value=}, {max_value=}")


def icu_order_by(db: Connector):
    """Benchmark using our custom collation, utf8mb4_nb_icu_ai_ci."""
    query = """
    SELECT * FROM my_project.test1_no_NO
    ORDER BY value COLLATE utf8mb4_nb_icu_ai_ci
    DESC LIMIT 1;
    """

    log.info("Test: order_by_utf8mb4_nb_icu_ai_ci")
    log.info(f"{query=} | {repetitions=}")

    @time_this
    def order_by_utf8mb4_nb_icu_ai_ci():
        for _ in range(repetitions):
            db.cursor.execute(query)
            result = db.cursor.fetchall()
        return result

    result = order_by_utf8mb4_nb_icu_ai_ci()
    log.info(f"Result: {result}")


def icu_equals(db: Connector):
    """Benchmark using our custom collation, utf8mb4_nb_icu_ai_ci."""
    query = """
    SELECT * FROM my_project.test1_no_NO
    WHERE value = 'Norge123' COLLATE utf8mb4_nb_icu_ai_ci;
    """

    log.info("Test: equals_utf8mb4_nb_icu_ai_ci")
    log.info(f"{query=} | {repetitions=}")

    @time_this
    def equals_utf8mb4_nb_icu_ai_ci():
        for _ in range(repetitions):
            db.cursor.execute(query)
            result = db.cursor.fetchall()
        return result

    result = equals_utf8mb4_nb_icu_ai_ci()
    log.info(f"Result: {result}")


def mysql_order_by(db: Connector):
    """Benchmark using the MySQL collation utf8mb4_nb_0900_ai_ci."""
    query = """
    SELECT * FROM my_project.test1_no_NO
    ORDER BY value COLLATE utf8mb4_nb_0900_ai_ci
    DESC LIMIT 1;
    """

    log.info("Test: order_by_utf8mb4_nb_0900_ai_ci")
    log.info(f"{query=} | {repetitions=}")

    @time_this
    def order_by_utf8mb4_nb_0900_ai_ci():
        for _ in range(repetitions):
            db.cursor.execute(query)
            result = db.cursor.fetchall()
        return result

    result = order_by_utf8mb4_nb_0900_ai_ci()
    log.info(f"Result: {result}")


def mysql_equals(db: Connector):
    """Benchmark using the MySQL collation utf8mb4_nb_0900_ai_ci."""
    query = """
    SELECT * FROM my_project.test1_no_NO
    WHERE value = 'Norge123' COLLATE utf8mb4_nb_0900_ai_ci;
    """

    log.info("Test: equals_utf8mb4_nb_0900_ai_ci")
    log.info(f"{query=} | {repetitions=}")

    @time_this
    def equals_utf8mb4_nb_0900_ai_ci():
        for _ in range(repetitions):
            db.cursor.execute(query)
            result = db.cursor.fetchall()
        return result

    result = equals_utf8mb4_nb_0900_ai_ci()
    log.info(f"Result: {result}")
