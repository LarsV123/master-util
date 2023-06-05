"""Script for extracting symbols used in tailorings from ctype-icu-tailorings.h"""

import re
import os
from utils.custom_logger import log


def extract_and_split_strings():
    filename = os.path.expanduser("~/mysql/mysql-server/strings/ctype-icu-tailorings.h")
    log.debug(f"{filename=}")

    with open(filename, "r") as f:
        content = f.read()

    pattern = r'"(.*?)"'
    matches = re.findall(pattern, content)

    split_symbols = ["&", "[", "]", "*", "<"]
    result = []
    for match in matches:
        split_strings = re.split("|".join(map(re.escape, split_symbols)), match)
        result.extend([s for s in split_strings if s])

    return result
