import argparse
import json
from lxml import etree

VERSION_NUM = "0.2.0"
SPEC_NAME = "USJ" # for Unified Scripture JSON

def convert_usx(input_usx_elmt):
    '''Accepts an XML object of USX and returns a Dict corresponding to it.
    Traverses the children, recursively'''
    key = input_usx_elmt.tag
    if key in ['row', 'cell']:
        key = "table:"+key
    text = None
    out_obj = {}
    action = "append"
    attribs = dict(input_usx_elmt.attrib)
    tag = None
    if "style" in attribs:
        if attribs["style"] == 'b':
            key = "optbreak"
        tag = attribs['style']
        del attribs['style']
    if "vid" in attribs:
        del attribs['vid'] # dropping because presence of vid in paragraph elements is not consistent in USX
    if "closed" in attribs:
        del attribs['closed']
    if "status" in attribs:
        del attribs['status']
    out_obj["type"]  = key
    if tag:
        out_obj["marker"] = tag
    out_obj =  out_obj | attribs
    if input_usx_elmt.text and input_usx_elmt.text.strip() != "":
        text = input_usx_elmt.text.strip()
    children = input_usx_elmt.getchildren()
    out_obj['content'] = []
    if text:
        out_obj['content'].append(text)
    for child in children:
        child_dict, what_to_do = convert_usx(child)
        match what_to_do:
            case "append":
                out_obj['content'].append(child_dict)
            case "merge":
                out_obj['content'] += child_dict
            case "ignore":
                pass
            case _:
                pass
        if child.tail and child.tail.strip() != "":
            out_obj['content'].append(child.tail.strip())
    if  (key in ["chapter", "verse", "optbreak", "ms"] or tag in ["va", "ca"])\
         and out_obj['content'] == []:
        del out_obj['content']
    if "eid" in out_obj and key in ['verse', 'chapter']:
        action = "ignore"
    # May need some special handling for va vp, ca cp elements.
    # Now the USX samples in testsuite are not correct
    return out_obj, action

def usx_to_json(input_usx):
    '''The core function for the process.
    input: parsed XML element for the whole USX
    output: dict object as per the JSON schema'''
    output_json, _ = convert_usx(input_usx)
    output_json['type'] = SPEC_NAME
    output_json['version'] = VERSION_NUM
    return output_json

def main():
    '''Handles the command line requests.
    Reads USX from a file and writes JSON to a file or prints to console'''
    arg_parser = argparse.ArgumentParser(
        description='Takes in a USX file and converts it into a JSON')
    arg_parser.add_argument('infile', type=str, help='input USX(.xml) file')
    arg_parser.add_argument('--output_path', type=str, help='path to write the output file to',
        default="STDOUT")

    infile = arg_parser.parse_args().infile
    outpath = arg_parser.parse_args().output_path

    try:
        input_usx = etree.parse(infile)
    except Exception as exe:
        raise Exception("Input file path or the USX file seems not valid!") from exe

    output_json = usx_to_json(input_usx.getroot())
    json_str = json.dumps(output_json, ensure_ascii=False, indent=2)
    if outpath == 'STDOUT':
        print(json_str)
    else:
        with open(outpath, 'w', encoding='utf-8') as out_file:
            out_file.write(json_str)

if __name__ == '__main__':
    main()
