from .base import WiktParser
import logging
import json


class NamespacesParser(WiktParser):
    file_pattern = r"^enwiktionary-\d+-siteinfo-namespaces.json\.gz$"

    def setup(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """
        drop table if exists parsed_namespaces;
        """
        )
        c.execute(
            """
        create table parsed_namespaces (
            id integer,
            ns_case text,
            canonical text,
            star text,
            content text,
            subpages text,
            namespaceprotection text,
            defaultcontentmodel text
        );
        """
        )
        conn.commit()
        conn.close()

    def parse_file(self, fpath) -> None:
        self.assert_file_pattern_match(fpath)
        self.setup()
        logging.info(f"Namespaces: Parsing {fpath}")
        unzipped = self.copy_and_gunzip(fpath)
        logging.info(f"Namespaces: reading json")
        with open(unzipped, "r") as f:
            d = json.loads(f.read())
        tups = []
        for ns in d["query"]["namespaces"].values():
            tups.append(
                (
                    ns.get("id", None),
                    ns.get("case", None),
                    ns.get("canonical", None),
                    ns.get("*", None),
                    ns.get("content", None),
                    ns.get("subpages", None),
                    ns.get("namespaceprotection", None),
                    ns.get("defaultcontentmodel", None),
                )
            )
        for i in range(len(tups[0])):
            found_non_none = False
            for tup in tups:
                if tup[i] is not None:
                    found_non_none = True
                    break
            if not found_non_none:
                raise ValueError(f"no nonnull values found for index {i}")
        logging.info(f"Namespaces: Inserting rows")
        conn = self.get_connection()
        c = conn.cursor()
        c.executemany("insert into parsed_namespaces values (?,?,?,?,?,?,?,?)", tups)
        conn.commit()
        conn.close()
        self.cleanup()
        logging.info(f"Namespaces: complete")
