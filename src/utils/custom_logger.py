import logging

# Set up default logger for project
formatter = logging.Formatter("[%(levelname)s]\t %(message)s")
log = logging.getLogger("mysql-util")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)
