import csv
import os
from argparse import ArgumentParser

from ucca import layer0, layer1
from ucca.ioutil import get_passages_with_progress_bar, write_passage
from ucca.normalization import fparent

desc = """Change articles to Function, complying with UCCA v2 guidelines"""

ARTICLES = {
    "de": ("der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "eines"),
    "en": ("a", "an", "the"),
}


def change_article_to_function(terminal, parent, lang):
    if terminal.text.lower() in ARTICLES[lang]:
        for edge in parent.incoming:
            if not edge.attrib.get("remote"):
                for category in edge.categories:
                    if category.tag == layer1.EdgeTags.Elaborator:
                        category.tag = layer1.EdgeTags.Function
                        return True


RULES = (change_article_to_function,)


def convert_passage(passage, lang, report_writer):
    for rule in RULES:
        for terminal in passage.layer(layer0.LAYER_ID).all:
            parent = fparent(terminal)
            if len(parent.children) == 1 and rule(terminal, parent, lang):
                report_writer.writerow((rule.__name__, passage.ID, terminal.ID, parent, fparent(terminal)))


def main(args):
    os.makedirs(args.outdir, exist_ok=True)
    with open(args.outfile, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("rule", "passage", "terminal", "before", "after"))
        for passage in get_passages_with_progress_bar(args.passages, desc="Converting"):
            convert_passage(passage, lang=passage.attrib.get("lang", args.lang), report_writer=writer)
            write_passage(passage, outdir=args.outdir, prefix=args.prefix, verbose=args.verbose)
            f.flush()
    print("Wrote '%s'" % args.outfile)


if __name__ == "__main__":
    argparser = ArgumentParser(description=desc)
    argparser.add_argument("passages", nargs="+", help="the corpus, given as xml/pickle file names")
    argparser.add_argument("-l", "--lang", choices=ARTICLES, help="two-letter language code for article list")
    argparser.add_argument("-o", "--outdir", default=".", help="output directory")
    argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
    argparser.add_argument("-O", "--outfile", default=os.path.splitext(argparser.prog)[0] + ".csv", help="log file")
    argparser.add_argument("-v", "--verbose", action="store_true", help="print tagged text for each passage")
    main(argparser.parse_args())
