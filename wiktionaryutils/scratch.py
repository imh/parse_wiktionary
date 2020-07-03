# In[0]:
import xml

# In[]:
# pip install lxml beautifulsoup4
# from bs4 import BeautifulSoup
# soup = BeautifulSoup(markup, "lxml-xml")
import xml.etree.ElementTree as ET

tree = ET.parse("/home/ubuntu/enwiktionary-20200620-pages-meta-current.xml")
root = tree.getroot()

# In[]:
elems = []
for i, ch in enumerate(root):
    elems.append(ch)
    if i > 20:
        break

# In[]:
ch = elems[3]
print("tag:", ch.tag, ",attrib: ", ch.attrib, ", text: ", ch.text, ", len(): ", len(ch))
list(ch)

# In[]:
for ch in elems:
    assert ch.tag == "doc"
    lch = list(ch)
    assert lch[0].tag == "title"
    assert lch[1].tag == "url"
    assert lch[2].tag == "abstract"
    assert lch[3].tag == "links"
    title = lch[0].text
    url = lch[1].text
    abstract = lch[2].text
    links = lch[3]

# In[]:
known_tags = {
    "{http://www.mediawiki.org/xml/export-0.10/}title",
    "{http://www.mediawiki.org/xml/export-0.10/}ns",
    "{http://www.mediawiki.org/xml/export-0.10/}id",
    "{http://www.mediawiki.org/xml/export-0.10/}restrictions",
    # '{http://www.mediawiki.org/xml/export-0.10/}redirect',
    "{http://www.mediawiki.org/xml/export-0.10/}revision",
}


def check_types(elem):
    for gch in elem:
        assert gch.tag in known_tags


h, *t = root
for elem in t:
    check_types(elem)

# In[]:
import json


def parse_elem(elem):
    d = {}
    for ch in elem:
        d[ch.tag] = ch
    # title
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
        rev_d[gch] = gch
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
