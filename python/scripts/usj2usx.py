'''Standalone script to generate USX from input USJ'''

import glob
import argparse
import json
from jsonschema import validate
import re
import lxml.etree


USJ_SCHEMA = None
with open('grammar/usj.js', 'r', encoding='utf-8') as json_file:
    USJ_SCHEMA = json.load(json_file)

prev_chapter_sid = None
prev_verse_sid = None

VERSE_CARRYING_PARAS = [
       "q", "qr", "qc", "qa", "qm", "qd", #poetry
        "lh", "li", "lf", "lim", "litl", #lists
        "tr", "tc", "th", "tcr", "thr", # table
        "p", "m", "po", "pr", "cls", "pmo", "pm",
        "pmc", "pmr", "pi", "mi", "nb", "pc", "ph", 
        ]

def find_para_node_for_verse_eid(current_usx_head):
    if current_usx_head.tag in ["para", "cell"] and \
        (len(current_usx_head) > 0 or current_usx_head.text is not None): # within a para
        return current_usx_head
    if current_usx_head.tag in ["para", "cell"] and len(current_usx_head) == 0: # start of a para
        paras = current_usx_head.getparent().xpath('para | .//cell')[:-1]
    else:
        paras = current_usx_head.xpath('para | .//cell') # not in a para element
    for i in range(len(paras)-1, -1, -1):
        if "style" in paras[i].attrib:
            marker = re.sub(r'\d+$', "", paras[i].attrib['style'])
        if (paras[i].tag == "table" or marker in VERSE_CARRYING_PARAS) and \
                (len(paras[i]) > 0 or paras[i].text is not None):
            return paras[i]
    raise Exception("Can't find a suitable last para:\n "+\
        f"{lxml.etree.tostring(current_usx_head)}")


def convert_usj(json_node, usx_head):
    '''Traverse the JSON recursively, building the XML'''
    global prev_verse_sid
    global prev_chapter_sid
    if json_node['type'] in ["chapter", "verse", "sidebar"]: # adding end nodes
        if prev_verse_sid is not None:
            end_node = lxml.etree.Element('verse')
            end_node.set('eid', prev_verse_sid)
            last_para = find_para_node_for_verse_eid(usx_head)
            last_para.append(end_node)
        if json_node['type'] == 'verse':
            prev_verse_sid = json_node["sid"]
        else:
            prev_verse_sid = None
        if json_node['type'] == "chapter":
            if prev_chapter_sid is not None:
                end_node = lxml.etree.SubElement(usx_head, 'chapter')
                end_node.set('eid', prev_chapter_sid)    
            prev_chapter_sid = json_node['sid']

    if json_node['type'] in ['table:row', 'table:cell']:
        json_node['type'] = json_node['type'].replace("table:", "")

    if json_node['type'] == 'optbreak':
        json_node['type'] = "para"
    new_node = lxml.etree.SubElement(usx_head, json_node['type'])
    if 'marker' in json_node:
        new_node.set('style', json_node['marker'])
    for key in json_node:
        if key not in ['type', 'marker', 'content']:
            new_node.set(key, json_node[key])
    if 'content' in json_node:
        for item in json_node['content']:
            if isinstance(item, str):
                if len(new_node) == 0:
                    new_node.text = item
                else:
                    new_node[-1].tail = item
            else:
                convert_usj(item, new_node)

def usj_to_xml(input_usj):
    '''Build the XML tree'''
    global prev_verse_sid
    global prev_chapter_sid
    prev_verse_sid = None
    prev_chapter_sid = None
    output_usx = lxml.etree.Element('usx')
    output_usx.set('version', '3.0')
    for item in input_usj['content']:
        convert_usj(item, output_usx)

    # adding end nodes for verse and chapter as those are not in USJ
    if prev_verse_sid is not None:
        end_node = lxml.etree.Element('verse')
        end_node.set('eid', prev_verse_sid)
        last_para = find_para_node_for_verse_eid(output_usx)
        last_para.append(end_node)
    if prev_chapter_sid is not None:
        end_node = lxml.etree.SubElement(output_usx, 'chapter')
        end_node.set('eid', prev_chapter_sid)    

    return output_usx

def test():
    '''Test by comparing the generated USX against origin.xml in test suite'''
    from lxml.doctestcompare import LXMLOutputChecker
    checker = LXMLOutputChecker()
    usj_paths = glob.glob('tests/*/*/origin.json') + glob.glob('tests/*/*/*/origin.json')
    conversion_error = 0
    comparison_error = 0
    for path in usj_paths:
        with open(path, 'r', encoding='utf-8') as usj_file:
            input_usj = json.load(usj_file)
            # validate(instance=input_usj, schema=USJ_SCHEMA)
            try:
                output_usx = usj_to_xml(input_usj)
            except Exception as exce:
                conversion_error += 1
                print(f"\n\nError at {path}\n{exce}")
                continue
                # raise Exception(f"Error at conversion on {path}") from exce
        with open(path.replace('.json','.xml'), 'r', encoding='utf-8') as origin_file:
            origin_usx = lxml.etree.parse(origin_file).getroot()
            all_vid_nodes = origin_usx.findall(".//*[@vid]")
            all_closed_nodes = origin_usx.findall(".//*[@closed]")
            all_status_nodes = origin_usx.findall(".//*[@status]")
            for node in all_vid_nodes:
                del node.attrib['vid']
            for node in all_closed_nodes:
                del node.attrib['closed']
            for node in all_status_nodes:
                del node.attrib['status']
        if not checker.compare_docs(origin_usx, output_usx):
            comparison_error += 1
            message = checker.collect_diff(origin_usx, output_usx, html=False, indent=4)
            print(f"\n\nError at {path}\n{message}")
    print(f"{conversion_error=}\n{comparison_error=}")
    print(f"Out of total tested {len(usj_paths)} samples.")


def main():
    '''Handles the command line requests.
    Reads USX from a file and writes JSON to a file or prints to console'''
    arg_parser = argparse.ArgumentParser(
        description='Takes in a USJ file and converts it into corresponding USX')
    arg_parser.add_argument('infile', type=str, help='input USJ(.json) file')
    arg_parser.add_argument('--output_path', type=str, help='path to write the output file to',
        default="STDOUT")

    infile = arg_parser.parse_args().infile
    outpath = arg_parser.parse_args().output_path

    try:
        with open(infile, 'r', encoding='utf-8') as usj_file:
            input_usj = json.load(usj_file)
    except Exception as exe:
        raise Exception("Input file path or the USJ file seems not valid!") from exe

    try:
        validate(instance=input_usj, schema=USJ_SCHEMA)
    except Exception as exce:
        raise Exception("Input USJ format is not valid!") from exce

    
    output_usx = usj_to_xml(input_usj)
    xmlstr = lxml.etree.tostring(output_usx,
                encoding='unicode', pretty_print=True)
    if outpath == 'STDOUT':
        print(xmlstr)
    else:
        with open(outpath, 'w', encoding='utf-8') as out_file:
            out_file.write(xmlstr)

if __name__ == '__main__':
    main()
    # test()
