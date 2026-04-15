import os
import shutil
import glob

from tqdm import tqdm
from acdh_tei_pyutils.tei import TeiReader
from acdh_xml_pyutils.xml import NSMAP as nsmap

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
    new_name = f"TLx-{part:01}.xml"
    doc = TeiReader(x)
    for i, y in enumerate(doc.any_xpath(".//tei:pb")):
        y.attrib["n"] = f"TLx-{part:01}_{img_lookup[i]}"
    for i, y in enumerate(doc.any_xpath(".//tei:surface[@xml:id]")):
        graphic = y.xpath(".//tei:graphic", namespaces=nsmap)[0]
        graphic.attrib["url"] = f"TLx-{part:01}_{img_lookup[i]}"
    save_path = os.path.join(new_items, new_name)
    doc.tree_to_file(save_path)


files = glob.glob('./data/new_items/*.xml')
print("fixing facs")
for x in tqdm(files):
    doc = TeiReader(x)
    facs_url = doc.any_xpath(".//tei:graphic/@url")[0]
    pb = doc.any_xpath(".//tei:pb")[0]
    pb.attrib["corresp"] = f"{arche_base}{facs_url}"
    doc.tree_to_file(x)


print("renaming files")
files = sorted(glob.glob('./data/new_items/*.xml'))
for i, x in enumerate(files, start=1):
    doc = TeiReader(x)
    cur_id = f"TL-{i:04}"
    f_name = f"{cur_id}.xml"
    graphic = doc.any_xpath(".//tei:graphic")[0]
    graphic.attrib["url"] = f"{cur_id}.jpg"

    pb = doc.any_xpath(".//tei:pb")[0]
    pb.attrib["facs"] = f"#{cur_id}.jpg"
    doc.tree_to_file(os.path.join("data", "new_items", f_name))
    os.remove(x)

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

