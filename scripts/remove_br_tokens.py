#!/usr/bin/env python3

import ntpath
import argparse
import os
from xml.etree.ElementTree import tostring

from ucca import convert
from ucca.ioutil import external_write_mode
from ucca.ioutil import get_passages_with_progress_bar
import xml.etree.ElementTree as ET

desc = """Removes <br> tokens from a standard XML."""


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    for fn in args.filenames:
        tree = ET.parse(fn)
        root = tree.getroot()
        to_remove = []
        for node in root.getiterator():
            if node.tag == 'layer' and node.attrib.get('layerID',None) == "0":
                layer0 = node
            if node.tag == 'node':
                for e in node.iter():
                    if e.tag == 'attributes':
                        if e.attrib.get('text',None) in ['','<br>']:
                            to_remove.append(node)
        for node in to_remove:
            layer0.remove(node)
        xml_str = tostring(root).decode()
        site_filename = os.path.join(args.outdir,ntpath.basename(fn))
        f = open(site_filename,'w')
        f.write(xml_str)
        f.close()



if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="XML file names to convert")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    main(argparser.parse_args())
