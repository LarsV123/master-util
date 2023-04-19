"""
Util functions for performance testing with perf.
"""


def perf_benchmark(collation: str, locale: str):
    """
    Run simplified performance benchmarks to provide data for
    perf.
    """
    configuration = {
        "collation": collation,
        "locale": locale,
        "data_table": f"test_{locale}_10000000",
    }
