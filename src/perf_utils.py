from benchmarks import test_collation
from utils.custom_logger import log
from db import Connector
from tqdm import tqdm

"""
Util functions for performance testing with perf.
"""


def perf_load_test(collation: str):
    """
    Run simplified performance benchmarks to provide data for
    perf.
    """
    configuration = {
        "collation": collation,
        "locale": "en_US",
        "data_table": "test_en_US_10000000",
        "data_size": 0,
        "tailoring_size": 0,
    }

    log.info("Running stresstest...")
    conn = Connector()
    for _ in tqdm(range(3)):
        test_collation(conn, configuration)
    log.info("Finished running stresstest.")
