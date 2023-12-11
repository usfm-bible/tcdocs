
from usfmtc.xmlutils import ParentElement

def usxtousj(input_usx_elmt):
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
    out_obj['content'] = []
    if text:
        out_obj['content'].append(text)
    for child in input_usx_elmt:
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

def usjtousx(adict, elfactory=None):
    if elfactory is None:
        elfactory = ParentElement       # Needed for adding esid_s. Or use lxml
    return None
