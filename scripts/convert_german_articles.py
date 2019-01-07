import csv
import os
from argparse import ArgumentParser

from ucca import layer0, layer1
from ucca.ioutil import get_passages_with_progress_bar, write_passage
from ucca.normalization import fparent

desc = """Convert the German Der kleine Prinz"""

ARTICLES = (
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "eines"
)


def change_article_to_function(terminal, parent):
    if terminal.text.lower() in ARTICLES and parent.ftag == layer1.EdgeTags.Elaborator:
        parent.incoming[0].tag = layer1.EdgeTags.Function
        return True


RULES = (change_article_to_function,)


def convert_passage(passage, report_writer):
    for rule in RULES:
        for terminal in passage.layer(layer0.LAYER_ID).all:
            parent = fparent(terminal)
            if len(parent.children) == 1 and rule(terminal, parent):
                report_writer.writerow((rule.__name__, passage.ID, terminal.ID, parent, fparent(terminal)))


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    with open(args.outfile, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("rule", "passage", "terminal", "before", "after"))
        for passage in get_passages_with_progress_bar(args.passages, desc="Converting"):
            convert_passage(passage, report_writer=writer)
            write_passage(passage, outdir=args.outdir, prefix=args.prefix, verbose=args.verbose)
            f.flush()
    print("Wrote '%s'" % args.outfile)


if __name__ == "__main__":
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
    argparser.add_argument("-O", "--outfile", default=os.path.splitext(argparser.prog)[0] + ".csv", help="log file")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
