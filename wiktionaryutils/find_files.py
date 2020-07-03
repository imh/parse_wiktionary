import os
import re
import logging
from .parsers import WiktParser
from typing import List, Dict
from collections import defaultdict


def log_elements_found(cat: str, f_list):
    if len(f_list) == 0:
        logging.info(f"No {cat}s.")
        return
    logging.info(f"Found {len(f_list)} {cat}s:")
    for f in f_list:
        logging.info(f"{cat}: {f}")


def find_files(
    data_home: str, parsers: List[WiktParser]
) -> Dict[WiktParser, List[str]]:

    found_files = os.listdir(data_home)
    file2parser = {}
    parser2files = defaultdict(list)
    for parser in parsers:
        for file in found_files:
            if re.match(parser.file_pattern, file):
                if file in file2parser:
                    raise Exception(
                        f"file {file} is matches at least two parsers. {type(file2parser[file])} and {type(parser)}."
                    )
                file2parser[file] = parser
                parser2files[parser].append(os.path.join(data_home, file))
    unrecognized_files = [f for f in found_files if f not in file2parser]
    log_elements_found("unrecognized file", unrecognized_files)
    for parser, files in parser2files.items():
        log_elements_found(f"{parser.__class__.__name__}-parseable file", files)
    unused_parsers = [p.__class__.__name__ for p in parsers if p not in parser2files]
    log_elements_found("unused parser", unused_parsers)
    return parser2files
