import os
import shutil
import glob
import lxml.etree as ET

from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm
from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import nsmap

environment = Environment(loader=FileSystemLoader("./"))
template = environment.get_template("template.j2")
arche_base = "https://id.acdh.oeaw.ac.at/tillich-lectures/"
editions = os.path.join("data", "editions")
shutil.rmtree(editions, ignore_errors=True)
os.makedirs(editions, exist_ok=True)


col_id = "271480"
files = sorted(glob.glob("./tei/*.xml"))
for part, x in enumerate(files, start=1):
    tei_name = os.path.split(x)[-1]
    mets_name = f'{os.path.join("mets", col_id, tei_name.replace(".xml", "_image_name.xml"))}'
    mets = TeiReader(mets_name)
    img_lookup = [x.text for x in mets.any_xpath(".//item")]
    doc = TeiReader(x)
    for i, y in enumerate(doc.any_xpath(".//tei:pb")):
        y.attrib["n"] = f"part{part:01}_{img_lookup[i]}"
    for i, y in enumerate(doc.any_xpath(".//tei:surface[@xml:id]")):
        graphic = y.xpath(".//tei:graphic", namespaces=nsmap)[0]
        graphic.attrib["url"] = f"part{part:01}_{img_lookup[i]}"
    doc.tree_to_file(x)

for i, x in enumerate(tqdm(files)):
    doc_id = os.path.split(x)[-1].replace('.xml', '')
    doc = TeiReader(x)
    nsmap = doc.nsmap
    for y in doc.any_xpath(".//tei:surface[@xml:id]"):
        facs_id = y.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        img_url = y.xpath("./tei:graphic/@url", namespaces=nsmap)[0]
        img_id = img_url.replace(".jpg", "")
        pb_node = doc.any_xpath(f'.//tei:pb[@facs="#{facs_id}"]')[0]
        xpath_expr = f'.//tei:ab[@facs="{facs_id}" or starts-with(@facs, "#{facs_id}_")]'
        ab_node = doc.any_xpath(xpath_expr)
        if len(ab_node) > 1:
            print(len(ab_node))
        ab_text = ""
        for abnode in ab_node:
            ab_text += (
                ET.tostring(abnode, encoding="utf-8")
                .decode("utf-8")
                .replace('key=", Personen ID=', 'ref="tillich-lectures__')
                .replace('xmlns="http://www.tei-c.org/ns/1.0"', "")
                .replace("vertical-align: superscript;", "superscript")
            )
            ab_text = ab_text.replace('ref="tillich-lectures', 'ref="#tillich-lectures')
        page = {
            "id": f"tillich-lectures-{img_id}",
            "col_id": col_id,
            "doc_id": doc_id,
            "img_id": img_id,
            "img_url": img_url,
            "surface_node": ET.tostring(y, encoding="utf-8")
            .decode("utf-8")
            .replace('xmlns="http://www.tei-c.org/ns/1.0"', ""),
            "pb_node": ET.tostring(pb_node, encoding="utf-8")
            .decode("utf-8")
            .replace('xmlns="http://www.tei-c.org/ns/1.0"', ""),
            "ab_node": ab_text,
        }
        content = template.render(**page)
        with open(os.path.join(editions, f"tillich-lectures-{img_id}.xml"), "w") as f:
            f.write(content)

files = glob.glob('./data/editions/*xml')
print("fixing facs")
for x in tqdm(files):
    doc = TeiReader(x)
    facs_url = doc.any_xpath(".//tei:graphic/@url")[0]
    pb = doc.any_xpath(".//tei:pb")[0]
    pb.attrib["corresp"] = f"{arche_base}{facs_url}"
    doc.tree_to_file(x)


files = sorted(glob.glob('./data/editions/*xml'))
for i, x in enumerate(files, start=1):
    doc = TeiReader(x)
    cur_id = f"TL-{i:04}"
    f_name = f"{cur_id}.xml"
    graphic = doc.any_xpath(".//tei:graphic")[0]
    graphic.attrib["url"] = f"{cur_id}.jpg"

    pb = doc.any_xpath(".//tei:pb")[0]
    pb.attrib["facs"] = f"#{cur_id}.jpg"
    doc.tree_to_file(os.path.join("data", "editions", f_name))
    os.remove(x)

files = sorted(glob.glob('./data/editions/*xml'))
for x in files:
    doc = TeiReader(x)
    body = doc.any_xpath(".//tei:body")[0]
    for element in body.iter():
        el_name = element.tag.replace("{http://www.tei-c.org/ns/1.0}", "")
        if el_name[0].isupper():
            print(el_name)
            element.tag = "{http://www.tei-c.org/ns/1.0}rs"
            element.attrib["type"] = "keyword"
            element.attrib["ref"] = f"#{el_name}"
    doc.tree_to_file(x)