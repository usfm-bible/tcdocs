'''Standalone script to generate USX from input USJ'''

import argparse
import json
import lxml.etree
from jsonschema import validate


USJ_SCHEMA = None
with open('../grammar/usj.js', 'r', encoding='utf-8') as json_file:
    USJ_SCHEMA = json.load(json_file)

prev_chapter_sid = None
prev_verse_sid = None

def convert_usj(json_node, usx_head):
    '''Traverse the JSON recursively, building the XML'''
    global prev_verse_sid
    global prev_chapter_sid
    if json_node['type'] in ["chapter", "verse"]: # adding end nodes
        if prev_verse_sid is not None:
            end_node = lxml.etree.Element('verse')
            end_node.set('eid', prev_verse_sid)
            if usx_head.tag == "para":
                last_para = usx_head
            else:
                last_para = usx_head.findall('para')[-1]
            last_para.append(end_node)
        prev_verse_sid = json_node["sid"]
        if json_node['type'] == "chapter":
            prev_verse_sid = None
            if prev_chapter_sid is not None:
                end_node = lxml.etree.SubElement(usx_head, 'chapter')
                end_node.set('eid', prev_chapter_sid)    
            prev_chapter_sid = json_node['sid']
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
    output_usx = lxml.etree.Element('usx')
    output_usx.set('version', '3.0')
    for item in input_usj['content']:
        convert_usj(item, output_usx)

    # adding end nodes for verse and chapter as those are not in USJ
    if prev_verse_sid is not None:
        end_node = lxml.etree.Element('verse')
        end_node.set('eid', prev_verse_sid)
        last_para = output_usx.findall('para')[-1]
        last_para.append(end_node)
    if prev_chapter_sid is not None:
        end_node = lxml.etree.SubElement(output_usx, 'chapter')
        end_node.set('eid', prev_chapter_sid)    

    return output_usx

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
