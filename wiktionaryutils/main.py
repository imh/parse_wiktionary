#!/usr/bin/env python
# coding: utf-8

# InI[1]:
import os
import sys
import re
from importlib import reload
from wiktionaryutils.find_files import find_files
from wiktionaryutils.parsers import (
    WiktSQLParser,
    AllTitlesParser,
    NamespacesParser,
    PageXMLParser,
)
import logging

# logging.basicConfig(filename="/home/ubuntu/wiktionary_parse.log", level=logging.INFO)
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="/home/ubuntu/wiktionary_parse.log",
)

DATA_HOME = "/home/ubuntu/data"
MYSQL2SQLITE_DIR = "/home/ubuntu/mysql2sqlite"
SQLITE_DB_PATH = "/home/ubuntu/wiktionary.db"


def main():
    if os.path.exists(SQLITE_DB_PATH):
        os.remove(SQLITE_DB_PATH)
    sql_parser = WiktSQLParser(
        sqlite_db_path=SQLITE_DB_PATH, mysql2sqlite_dir=MYSQL2SQLITE_DIR
    )
    alltitles_parser = AllTitlesParser(sqlite_db_path=SQLITE_DB_PATH)
    namespaces_parser = NamespacesParser(sqlite_db_path=SQLITE_DB_PATH)
    xml_parser = PageXMLParser(sqlite_db_path=SQLITE_DB_PATH)
    parser2files = find_files(
        DATA_HOME, parsers=[sql_parser, alltitles_parser, namespaces_parser, xml_parser]
    )
    for parser, files in parser2files.items():
        for file in files:
            # if file == '/home/ubuntu/data/enwiktionary-20200620-categorylinks.sql.gz':
            parser.parse_file(file)
            parser.cleanup()


if __name__ == "__main__":
    main()
