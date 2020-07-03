from abc import ABC
import re
import os
import sqlite3
from shutil import copyfile
import logging
import subprocess


class WiktParser(ABC):
    tmp_gz = "/tmp/wiktionary_file.gz"
    tmp_bz2 = "/tmp/wiktionary_file.bz2"

    def __init__(self, sqlite_db_path: str):
        self.sqlite_db_path = sqlite_db_path
        self.to_cleanup = []

    @property
    def file_pattern(self) -> str:
        raise NotImplemented

    def parse_file(self, fpath) -> None:
        raise NotImplemented

    def assert_file_pattern_match(self, fpath) -> None:
        assert re.match(self.file_pattern, os.path.split(fpath)[1])

    def get_connection(self):
        return sqlite3.connect(self.sqlite_db_path)

    def copy_and_gunzip(self, fpath):
        assert fpath.endswith(".gz")
        unzipped = self.tmp_gz[:-3]
        copyfile(fpath, self.tmp_gz)
        # copyfile(fpath, self.tmp_sql)
        logging.info(f"Parsing file: Unzipping")
        subprocess.run(["gunzip", "-df", self.tmp_gz])
        self.to_cleanup.append(unzipped)
        return unzipped

    def copy_and_bz2unzip(self, fpath):
        assert fpath.endswith(".bz2")
        unzipped = self.tmp_bz2[:-4]
        copyfile(fpath, self.tmp_bz2)
        logging.info(f"Parsing file: Unzipping")
        subprocess.run(["bzip2", "-d", self.tmp_bz2])
        self.to_cleanup.append(unzipped)
        return unzipped

    def cleanup(self):
        for f in self.to_cleanup:
            if os.path.exists(f):
                os.remove(f)
        self.to_cleanup = []
