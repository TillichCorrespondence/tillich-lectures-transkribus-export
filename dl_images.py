import glob
import os
import requests
from acdh_tei_pyutils.tei import TeiReader

img_dir = "../tillich-lectures-facs"
files = sorted(glob.glob("./data/editions/*.xml"))
os.makedirs(img_dir, exist_ok=True)
images = glob.glob(f"{img_dir}/*.jpg")
print(images)

failed = []
for x in files:
    doc = TeiReader(x)
    if len(doc.any_xpath(".//tei:graphic")) == 2:
        new_name = doc.any_xpath(".//tei:graphic/@url")[0]
        url = doc.any_xpath(".//tei:graphic/@url")[-1]
        print(url, new_name)
        save_path = f"{img_dir}/{new_name}"
        if os.path.exists(save_path):
            continue
        else:
            try:
                r = requests.get(url)
            except Exception as e:
                print(x, e)
                failed.append(x)
                continue
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(r.content)
            else:
                failed.append(x)
