from .base import WiktParser
import subprocess
from shutil import copyfile
import os
import re
import logging
from tqdm import tqdm


class WiktSQLParser(WiktParser):
    file_pattern = r"^enwiktionary-\d+-.*\.sql\.gz$"

    def __init__(self, sqlite_db_path: str, mysql2sqlite_dir: str):
        super(WiktSQLParser, self).__init__(sqlite_db_path)
        logging.info(
            f"Created SQL parser. SQLite db: {sqlite_db_path}, mysql2sqlite dir: {mysql2sqlite_dir}"
        )
        self.mysql2sqlite_dir = mysql2sqlite_dir

    def parse_file(self, fpath) -> None:
        self.assert_file_pattern_match(fpath)
        logging.info(f"Parsing SQL file: {fpath}")
        self.cleanup()
        unzipped = self.copy_and_gunzip(fpath)
        logging.info("SQL: parsing sql file")
        with open(unzipped, "r", errors="replace") as f:
            state = "no create yet"
            columns = []
            inserts = []
            for line in f:
                if state == "no create yet":
                    m = re.match("CREATE TABLE (`[^`]+`)", line)
                    if m:
                        tablename = m.groups()[0]
                        logging.info(f"SQL: found create table ({tablename}): {line}")
                        state = "in columns"
                elif state == "in columns":
                    m = re.match("  (`[^`]+`) ([^ ]+)", line)
                    if m:
                        colname, coltype = m.groups()
                        if coltype.lower().startswith(
                            "varbinary"
                        ) or coltype.lower().startswith("binary"):
                            coltype = "blob"
                        if coltype.lower().startswith("enum("):
                            coltype = "text"
                        logging.info(f"SQL: found column ({colname} {coltype}): {line}")
                        columns.append((colname, coltype))
                    else:
                        state = "insertions"
                        logging.info("Looking for/adding insert statements.")
                else:
                    assert state == "insertions"
                    m = re.match(f"^INSERT INTO {tablename} VALUES (.*)$", line)
                    if m:
                        vals = m.groups()[0]
                        vals = vals.replace(r"\\", r"\"")
                        vals = vals.replace(r"\'", "''")
                        vals = vals.replace(r"\\n", "\n")
                        vals = vals.replace(r"\\r", "\r")
                        vals = vals.replace(r'\\"', r"\"")
                        inserts.append(
                            (
                                f"INSERT INTO {tablename} VALUES {vals}".replace(
                                    r"\'", "''"
                                ),
                                line,
                            )
                        )
                        # logging.info(f"SQL: found insert statement")
        assert len(columns) > 0
        assert len(inserts) > 0

        conn = self.get_connection()
        c = conn.cursor()
        logging.info("SQL: creating table")
        col_str = ", ".join([f"{colname} {coltype}" for colname, coltype in columns])
        c.execute(
            f"""
        create table {tablename} (
            {col_str}
        );
        """
        )
        logging.info("SQL: beginning inserts")
        for insert, original_line in tqdm(inserts):
            try:
                c.execute(insert)
            except Exception as e:
                with open("/home/ubuntu/bad_line.sql", "w") as f:
                    f.write(insert)
                    f.write("\n")
                    f.write(original_line)
                raise e
        conn.commit()
        conn.close()
        logging.info("SQL: complete")
        # logging.info(f"Parsing SQL file: Inserting")
        # sqlite_sql = subprocess.Popen(
        #     [os.path.join(self.mysql2sqlite_dir, "mysql2sqlite"), unzipped],
        #     stdout=subprocess.PIPE,
        # )
        # try:
        #     write_sqlite = subprocess.run(
        #         ["sqlite3", "-batch", self.sqlite_db_path], stdin=sqlite_sql.stdout
        #     )
        # except subprocess.CalledProcessError:
        #     logging.error("SQL failed")
        self.cleanup()
        logging.info(f"Parsing SQL file: Completed")
