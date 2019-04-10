import argparse
import csv
import sys
from glob import glob
from itertools import groupby
from operator import attrgetter

import spacy

from ucca import layer0
from ucca.ioutil import get_passages_with_progress_bar

MATCH_THRESHOLD = .7


def main(args):
    nlp = spacy.load(args.lang)
    all_text = []
    for filename in glob(args.text) or [args.text]:
        with open(filename, encoding="utf-8") as f:
            try:
                all_text += [(line, set(word.orth_ for word in nlp(line)))
                             for line in map(str.strip, f) if line and not line.startswith("#")]
            except UnicodeDecodeError as e:
                raise IOError("Failed reading '%s'" % filename) from e
    out = open(args.out, "w", encoding="utf-8", newline="") if args.out else sys.stdout
    writer = csv.writer(out, delimiter="\t")
    for p in get_passages_with_progress_bar(args.filenames, desc="Matching", converters={}):
        passage_tokens = sorted(p.layer(layer0.LAYER_ID).all, key=attrgetter("position"))
        for paragraph, paragraph_tokens in groupby(passage_tokens, key=attrgetter("paragraph")):
            paragraph_tokens_text = [terminal.text for terminal in paragraph_tokens]
            paragraph_tokens_set = set(paragraph_tokens_text)
            text = max_match_text = None
            max_match = 0
            for candidate_text, candidate_tokens_set in all_text:
                match = len(paragraph_tokens_set.intersection(candidate_tokens_set))
                if match > max_match:
                    max_match_text = candidate_text
                    max_match = match
                    if match > MATCH_THRESHOLD * len(paragraph_tokens_set):
                        if text is not None:
                            raise ValueError("Multiple texts match passage %s, paragraph %d:\n%s\n%s" % (
                                p.ID, paragraph, text, candidate_text))
                        text = candidate_text
            if text is None:
                raise ValueError("Could not find text for passage %s, paragraph %d:\n%s\nBest match (%d%%):\n%s" % (
                    p.ID, paragraph, " ".join(paragraph_tokens_text),
                    100 * max_match / len(paragraph_tokens_set), max_match_text))
            writer.writerow((p.ID, paragraph, text))
    out.close()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Normalize UCCA passages")
    argparser.add_argument("text", help="file of text to match to")
    argparser.add_argument("filenames", nargs="+", help="files or directories of UCCA passages to match")
    argparser.add_argument("-o", "--out", default="text.tsv", help="output file")
    argparser.add_argument("-l", "--lang", default="en", help="spaCy language")
    main(argparser.parse_args())
