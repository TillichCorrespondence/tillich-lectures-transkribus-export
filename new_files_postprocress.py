import os
import shutil
import glob

from tqdm import tqdm
from acdh_tei_pyutils.tei import TeiReader
from acdh_xml_pyutils.xml import NSMAP as nsmap
from acdh_tei_pyutils.utils import normalize_string

arche_base = "https://id.acdh.oeaw.ac.at/tillich-lectures/"
new_items = os.path.join("data", "new_items")
shutil.rmtree(new_items, ignore_errors=True)
os.makedirs(new_items, exist_ok=True)

col_id = "1956124"
files = sorted(glob.glob("./tei/7*.xml"))


for part, x in enumerate(files, start=1):
    tei_name = os.path.split(x)[-1]
    mets_name = f'{os.path.join("mets", col_id, tei_name.replace(".xml", "_image_name.xml"))}'
    mets = TeiReader(mets_name)
    img_lookup = [x.text for x in mets.any_xpath(".//item")]
    new_name = f"TLx-{part:04}.xml"
    doc = TeiReader(x)
    for i, y in enumerate(doc.any_xpath(".//tei:pb")):
        y.attrib["n"] = f"TLx-{part:04}_{img_lookup[i]}"
    for i, y in enumerate(doc.any_xpath(".//tei:surface[@xml:id]")):
        graphic = y.xpath(".//tei:graphic", namespaces=nsmap)[0]
        graphic.attrib["url"] = f"TLx-{part:04}_{img_lookup[i]}"
    save_path = os.path.join(new_items, new_name)
    print(save_path)
    doc.tree_to_file(save_path)


files = glob.glob('./data/new_items/*.xml')
print("fixing facs")
for x in tqdm(files):
    doc = TeiReader(x)
    facs_url = doc.any_xpath(".//tei:graphic/@url")[0]
    pb = doc.any_xpath(".//tei:pb")[0]
    pb.attrib["corresp"] = f"{arche_base}{facs_url}"
    doc.tree_to_file(x)


print("keyword-elements to rs-elements")
files = sorted(glob.glob('./data/new_items/*.xml'))
for x in tqdm(files, total=len(files)):
    doc = TeiReader(x)
    body = doc.any_xpath(".//tei:body")[0]
    for element in body.iter():
        el_name = element.tag.replace("{http://www.tei-c.org/ns/1.0}", "")
        if el_name[0].isupper():
            element.tag = "{http://www.tei-c.org/ns/1.0}rs"
            element.attrib["type"] = "keyword"
            element.attrib["ref"] = f"#{el_name}"
        elif element.tag == "{http://www.tei-c.org/ns/1.0}ab":
            element.tag = "{http://www.tei-c.org/ns/1.0}p"
    doc.tree_to_file(x)


print("update tei-header")
files = sorted(glob.glob('./data/new_items/*.xml'))
for x in tqdm(files, total=len(files)):
    header_doc = TeiReader("tei-header.xml")
    doc = TeiReader(x)
    doc_title = doc.any_xpath(".//tei:seriesStmt/tei:title/text()")[0]
    title = header_doc.any_xpath(".//tei:title[@type='main']")[0]
    title.text = doc_title
    idno_transkribus = doc.any_xpath(".//tei:idno[@type='Transkribus']")[0].text
    idno_header = header_doc.any_xpath(".//tei:idno[@type='transkribus_doc_id']")[0]
    idno_header.text = idno_transkribus
    idno_header = header_doc.any_xpath(".//tei:idno[@type='transkribus_col_id']")[0]
    idno_header.text = col_id
    locus_node = header_doc.any_xpath(".//tei:locus")[0]
    locus_node.text = doc_title
    for bad in doc.any_xpath(".//tei:teiHeader"):
        bad.getparent().remove(bad)
    header = header_doc.any_xpath(".//tei:teiHeader")[0]
    doc.tree.getroot().insert(0, header)
    doc.tree_to_file(x)

print("fix person rs refs")
files = sorted(glob.glob('./data/new_items/*.xml'))
for x in tqdm(files, total=len(files)):
    doc = TeiReader(x)
    for y in doc.any_xpath(".//tei:rs[@type='person' and @key]"):
        orig_attr = y.attrib["key"]
        orig_attr
        person_id = orig_attr.split("tillich_person_id__")
        try:
            san_id = int(person_id[-1])
            y.attrib["ref"] = f"#tillich_person_id__{san_id}"
            del y.attrib["key"]
        except ValueError:
            pass
    doc.tree_to_file(x)
