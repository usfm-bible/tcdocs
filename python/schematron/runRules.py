from saxonche import *
from io import open

with PySaxonProcessor(license=False) as proc:
      xsltproc = proc.new_xslt30_processor()
      document = proc.parse_xml(xml_file_name="MilestoneCheckv2.sch")
      executable = xsltproc.compile_stylesheet(stylesheet_file="iso_abstract_expand.xsl")
      expandedXml = executable.transform_to_string(xdm_node=document)
      
      document = proc.parse_xml(xml_text=expandedXml)
      executable = xsltproc.compile_stylesheet(stylesheet_file="iso_svrl_for_xslt2.xsl")
      schemaXml = executable.transform_to_string(xdm_node=document)
      
      document = proc.parse_xml(xml_file_name="originLevels.xml")
      executable = xsltproc.compile_stylesheet(stylesheet_text=schemaXml)
      output = executable.transform_to_string(xdm_node=document)
      
      print(output)
      
