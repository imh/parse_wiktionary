from .base import WiktParser
import json
import logging
from tqdm import tqdm
import xml.etree.ElementTree as ET


def parse_elem(elem):
    d = {}
    for ch in elem:
        d[ch.tag] = ch
    _title = d["{http://www.mediawiki.org/xml/export-0.10/}title"]
    _ns = d["{http://www.mediawiki.org/xml/export-0.10/}ns"]
    _id = d["{http://www.mediawiki.org/xml/export-0.10/}id"]
    _revision = d["{http://www.mediawiki.org/xml/export-0.10/}revision"]
    _restrictions = d.get(
        "{http://www.mediawiki.org/xml/export-0.10/}restrictions", None
    )
    _redirect = d.get("{http://www.mediawiki.org/xml/export-0.10/}redirect", None)
    title = _title.text
    ns = _ns.text
    elem_id = _id.text
    restrictions = _restrictions.text if _restrictions is not None else None
    redirect_attrib = json.dumps(_redirect.attrib if _redirect is not None else {})
    rev_d = {}
    for gch in _revision:
        rev_d[gch.tag] = gch
    revision_id = rev_d["{http://www.mediawiki.org/xml/export-0.10/}id"].text
    revision_timestamp = rev_d[
        "{http://www.mediawiki.org/xml/export-0.10/}timestamp"
    ].text
    _revision_contributor = rev_d[
        "{http://www.mediawiki.org/xml/export-0.10/}contributor"
    ]
    revision_model = rev_d["{http://www.mediawiki.org/xml/export-0.10/}model"].text
    revision_format = rev_d["{http://www.mediawiki.org/xml/export-0.10/}format"].text
    revision_text = rev_d["{http://www.mediawiki.org/xml/export-0.10/}text"].text
    revision_text_attrib = json.dumps(
        rev_d["{http://www.mediawiki.org/xml/export-0.10/}text"].attrib
    )
    revision_sha1 = rev_d["{http://www.mediawiki.org/xml/export-0.10/}sha1"].text
    # fmt: off
    return (elem_id, title, ns,
            restrictions, redirect_attrib,
            revision_id, revision_timestamp,
            revision_model, revision_format,
            revision_text, revision_text_attrib,
            revision_sha1)
    # fmt: on


class PageXMLParser(WiktParser):
    file_pattern = r"^enwiktionary-\d+-pages-meta-current\.xml.bz2$"

    def setup(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute(
            """
        drop table if exists xml_namespaces;
        """
        )
        c.execute(
            """
        drop table if exists xml_pages;
        """
        )
        c.execute(
            ""
            """
        create table xml_namespaces (
            ns_key integer,
            ns_case text,
            ns_text text
        );
        """
        )
        c.execute(
            """
        create table xml_pages (
            id integer,
            title text,
            ns integer,
            restrictions text,
            redirect_attrib text,
            revision_id integer,
            revision_timestamp text,
            revision_model text,
            revision_format text,
            revision_text text,
            revision_text_attrib text,
            revision_sha1 text
        );
        """
        )
        conn.commit()
        conn.close()

    def parse_file(self, fpath) -> None:
        self.assert_file_pattern_match(fpath)
        self.setup()
        logging.info(f"XML: Parsing {fpath}")
        logging.info("XML: unzipping")
        unzipped = self.copy_and_bz2unzip(fpath)
        logging.info("XML: Reading XML into tree")
        tree = ET.parse(unzipped)
        root = tree.getroot()
        site_info, *pages = root
        logging.info("XML: Parsing namespaces")
        namespaces = list(site_info)[-1]
        assert namespaces.tag.endswith("namespaces")
        ns_tups = []
        for ns in namespaces:
            ns_attrib = ns.attrib
            ns_key = ns_attrib["key"]
            ns_case = ns_attrib["case"]
            ns_text = ns.text
            ns_tups.append((ns_key, ns_case, ns_text))
        conn = self.get_connection()
        c = conn.cursor()
        logging.info("XML: Inserting namespaces")
        c.executemany(
            """insert into xml_namespaces values
            (?, ?, ?)""",
            ns_tups,
        )
        conn.commit()
        conn.close()
        page_tups = []

        logging.info("XML: parsing pages")
        for page in tqdm(pages):
            page_tups.append(parse_elem(page))
        logging.info("XML: inserting pages")
        conn = self.get_connection()
        c = conn.cursor()
        c.executemany(
            """insert into xml_pages values (?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?,
            ?, ?,
            ?)""",
            page_tups,
        )
        conn.commit()
        conn.close()
        logging.info("XML: complete")
