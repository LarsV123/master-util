import os
import mysql.connector as mysql
from utils.custom_logger import log
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Connector:
    """
    Connects to the MySQL server, using credentials stored in
    environment variables.
    """

    def __init__(self):
        # Connect to the MySQL server
        self.connection = mysql.connect(
            host=os.environ.get("HOST"),
            port=os.environ.get("PORT"),
            database=os.environ.get("DATABASE"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
        )

        # Create a cursor
        self.cursor = self.connection.cursor()

        # Disable autocommit
        self.cursor.execute("SET autocommit=0;")

        # Check connection
        db_version = self.connection.get_server_info()
        self.cursor.execute("select database();")
        database_name = self.cursor.fetchone()[0]
        log.debug(f"Connected to MySQL version '{db_version}'")
        log.debug(f"Database name: '{database_name}'")

    def execute_script(self, filename):
        # Open and read the file as a single buffer
        file = open(filename, "r", encoding="utf-8")

        # Read lines and strip line breaks
        lines = [x.strip().replace("\n", "") for x in file.read().split(";")]

        # Remove empty lines
        sql = [x for x in lines if x]
        file.close()

        # Execute every command from the input file
        for command in sql:
            try:
                self.cursor.execute(command)
            except Exception as e:
                log.error("Command skipped: ", command)
                log.error(e)

    def close(self):
        self.cursor.close()
        self.connection.close()
        log.debug("Connection to MySQL database closed")
