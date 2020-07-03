from .base import WiktParser
import logging


class AllTitlesParser(WiktParser):
    file_pattern = r"^enwiktionary-\d+-all-titles\.gz$"

    def setup(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """
        drop table if exists parsed_alltitles;
        """
        )
        c.execute(
            """
        create table parsed_alltitles (
            page_namespace integer,
            page_title text
        );
        """
        )
        conn.commit()
        conn.close()

    def parse_file(self, fpath) -> None:
        self.assert_file_pattern_match(fpath)
        self.setup()
        logging.info(f"Alltitles: Parsing {fpath}")
        unzipped = self.copy_and_gunzip(fpath)
        logging.info(f"Alltitles: reading lines")
        with open(unzipped, "r") as f:
            header, *items = f.readlines()
            tups = []
            for i in items:
                if i.strip() != "":
                    while i.endswith("\n"):
                        i = i[:-1]
                    l, r = i.split("\t")
                    ns = int(l)
                    tups.append((ns, r))
        logging.info(f"Alltitles: Inserting rows")
        conn = self.get_connection()
        c = conn.cursor()
        c.executemany("insert into parsed_alltitles values (?,?)", tups)
        conn.commit()
        conn.close()
        self.cleanup()
        logging.info(f"Alltitles: complete")
