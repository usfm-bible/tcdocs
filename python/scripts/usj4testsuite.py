import glob, json
from lxml import etree
import usx2usj

usx_paths = glob.glob('../../tests/*/*/origin.xml') + glob.glob('../../tests/*/*/*/origin.xml')

problem_usxs = [
    '../../tests/usfmjsTests/esb/origin.xml',  # last verse text given outside of paragraph. 
    '../../tests/special-cases/empty-attributes/origin.xml',  # attributes treated as text content of marker
]

for usx_path in usx_paths:
    with open(usx_path, 'r', encoding='utf-8') as usx_file:
        usx_text = usx_file.read()
        if 'status="invalid"' in usx_text or usx_path in problem_usxs:
            continue
    outpath = "/".join(usx_path.split('/')[:-1])+"/origin-usj.json"
    usx = etree.parse(usx_path)
    dict_out = usx2usj.usx_to_json(usx.getroot())
    with open(outpath, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(dict_out, indent=2, ensure_ascii=False))

print("Stats\n------\n")

usfm_paths = glob.glob('../../tests/*/*/origin.usfm') + glob.glob('../../tests/*/*/*/origin.usfm')
print(f"USFM samples: {len(usfm_paths)}")
print(f"USX samples: {len(usx_paths)}")

usj_paths = glob.glob('../../tests/*/*/origin-usj.json') + \
            glob.glob('../../tests/*/*/*/origin-usj.json')
print(f"USJ samples generated only for: {len(usj_paths)}")
print("(Converted only where USX was present and did not have elements with status='invalid' or other issues in it.)")
