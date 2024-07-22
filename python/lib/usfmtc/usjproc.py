
from usfmtc.xmlutils import ParentElement

SPEC_NAME="USJ"
VERSION_NUM="3.1"

def usxtousj(input_usx):
    '''The core function for the process.
    input: parsed XML element for the whole USX
    output: dict object as per the JSON schema'''
    output_json, _ = convert_usx(input_usx)
    output_json['type'] = SPEC_NAME
    output_json['version'] = VERSION_NUM
    return output_json

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
        text = input_usx_elmt.text
    out_obj['content'] = []
    if text:
        out_obj['content'].append(text)
    for child in input_usx_elmt:
        child_dict, what_to_do = convert_usx(child)
        if what_to_do == "append":
            out_obj['content'].append(child_dict)
        elif what_to_do == "merge":
            out_obj['content'] += child_dict
        if child.tail and child.tail.strip() != "":
            out_obj['content'].append(child.tail)
    if  (key in ["chapter", "verse", "optbreak", "ms"] or tag in ["va", "ca", "b"])\
         and out_obj['content'] == []:
        del out_obj['content']
    if "eid" in out_obj and key in ['verse', 'chapter']:
        action = "ignore"
    # May need some special handling for va vp, ca cp elements.
    # Now the USX samples in testsuite are not correct
    return out_obj, action

def usjtousx(adict, elfactory=None):
    if elfactory is None:
        elfactory = ParentElement       # Needed for adding esid_s. Or use lxml
    root = elfactory('usx')
    root.set('version', '3.1')
    for item in adict['content']:
        convert_usj(item, root, elfactory)
    return root

def convert_usj(json_node, usx_head, elfactory):
    ntype = json_node['type'].replace('table:', '')
    new_node = elfactory(ntype, parent=usx_head)
    parent.append(new_node)
    if 'marker' in json_node:
        new_node.set('style', json_node['marker'])
    for k, v in json_node.items():
        if k not in ('type', 'marker', 'content'):
            new_node.set(k, v)
    if 'content' in json_node:
        for item in json_node['content']:
            if isinstance(item, str):
                if len(new_node) == 0:
                    new_node.text = item
                else:
                    new_node[-1].tail = item
            else:
                convert_usj(item, new_node, elfactory)
