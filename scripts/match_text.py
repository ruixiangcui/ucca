import argparse
import csv
import re
import sys
from glob import glob
from itertools import groupby
from operator import attrgetter

import spacy
from tqdm import tqdm

from ucca import layer0
from ucca.ioutil import get_passages_with_progress_bar


def gen_lines(filenames):
    for filename in glob(filenames) or [filenames]:
        with open(filename, encoding="utf-8") as f:
            try:
                for line in map(str.strip, f):
                    if line and not line.startswith("#"):
                        yield re.sub(r"\[\d+\]", "", line)  # Remove numbers inside brackets
            except UnicodeDecodeError as e:
                raise IOError("Failed reading '%s'" % filename) from e


class CandidateMatcher:
    def __init__(self, paragraph_tokens_set):
        self.paragraph_tokens_set = paragraph_tokens_set

    def __call__(self, doc):
        return len(self.paragraph_tokens_set.intersection(s.orth_ for s in doc))


def match_passage_text(passage, docs, writer):
    passage_tokens = sorted(passage.layer(layer0.LAYER_ID).all, key=attrgetter("position"))
    for paragraph, paragraph_tokens in groupby(passage_tokens, key=attrgetter("paragraph")):
        paragraph_tokens_text = [terminal.text for terminal in paragraph_tokens]
        matcher = CandidateMatcher(set(paragraph_tokens_text))
        doc = sub_doc = max(docs, key=matcher)
        match = matcher(doc)
        for start in range(len(doc)):
            if not doc[start].is_punct:
                for end in range(len(doc), start + 1, -1):
                    if matcher(doc[start:end]) < match:
                        break
                    sub_doc = doc[start:end]
        writer.writerow((passage.ID, str(sub_doc)))


def main(args):
    nlp = spacy.load(args.lang)
    docs = [nlp(line) for line in tqdm(list(gen_lines(args.text)), desc="Tokenizing " + args.text, unit=" lines")]
    out = open(args.out, "w", encoding="utf-8", newline="") if args.out else sys.stdout
    writer = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_NONE)
    for p in get_passages_with_progress_bar(args.filenames, desc="Matching", converters={}):
        match_passage_text(p, docs, writer)
    out.close()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Normalize UCCA passages")
    argparser.add_argument("text", help="file of text to match to")
    argparser.add_argument("filenames", nargs="+", help="files or directories of UCCA passages to match")
    argparser.add_argument("-o", "--out", default="text.tsv", help="output file")
    argparser.add_argument("-l", "--lang", default="en", help="spaCy language")
    main(argparser.parse_args())
