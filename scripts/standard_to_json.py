#!/usr/bin/env python3

import argparse
import os

from ucca import convert
from ucca.ioutil import external_write_mode
from ucca.ioutil import get_passages_with_progress_bar

desc = """Parses an XML in UCCA standard format, and writes them in new site format."""


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    for passage in get_passages_with_progress_bar(args.filenames):
        site_filename = os.path.join(args.outdir, passage.ID + ".json")
        with open(site_filename, "w", encoding="utf-8") as f:
            print("\n".join(convert.to_json(passage)), file=f)
        if args.verbose:
            with external_write_mode():
                print("Wrote '%s'" % site_filename)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+", help="XML file names to convert")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    main(argparser.parse_args())
