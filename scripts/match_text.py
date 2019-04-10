import argparse
import csv
import sys
from glob import glob
from itertools import groupby
from operator import attrgetter

import spacy
from tqdm import tqdm

from ucca import layer0
from ucca.ioutil import get_passages_with_progress_bar

MATCH_THRESHOLD = .7


def gen_lines(filenames):
    for filename in glob(filenames) or [filenames]:
        with open(filename, encoding="utf-8") as f:
            try:
                for line in map(str.strip, f):
                    if line and not line.startswith("#"):
                        yield line
                        # yield re.sub(r"\[[^]]*\]", "", line)  # Remove anything inside brackets
            except UnicodeDecodeError as e:
                raise IOError("Failed reading '%s'" % filename) from e


def match_passage_text(passage, docs, writer):
    passage_tokens = sorted(passage.layer(layer0.LAYER_ID).all, key=attrgetter("position"))
    for paragraph, paragraph_tokens in groupby(passage_tokens, key=attrgetter("paragraph")):
        paragraph_tokens_text = [terminal.text for terminal in paragraph_tokens]
        paragraph_tokens_set = set(paragraph_tokens_text)
        text = max_match_text = None
        max_match = 0
        for doc, token_set in docs:
            match = len(paragraph_tokens_set.intersection(s.orth_ for s in doc))
            if match > max_match:
                max_match_text = str(doc)
                max_match = match
                if match > MATCH_THRESHOLD * len(paragraph_tokens_set):
                    if text is not None:
                        raise ValueError("Multiple texts match passage %s, paragraph %d:\n%s\n%s\n%s" % (
                            passage.ID, paragraph, " ".join(paragraph_tokens_text), text, doc))
                    text = str(doc)
                    # for start in range(len(doc)):
                    #     for end in range(len(doc), start + 1, -1):
                    #         if doc[start].orth_ == paragraph_tokens_text[0] and \
                    #                 doc[end - 1].orth_ == paragraph_tokens_text[-1]:
                    #             match = len(paragraph_tokens_set.intersection(s.orth_ for s in doc[start:end]))
                    #             if match > MATCH_THRESHOLD * len(paragraph_tokens_set):
                    #                 text = str(doc[start:end])
        if text is None:
            raise ValueError("Could not find text for passage %s, paragraph %d:\n%s\nBest match (%d%%):\n%s" % (
                passage.ID, paragraph, " ".join(paragraph_tokens_text),
                100 * max_match / len(paragraph_tokens_set), max_match_text))
        writer.writerow((passage.ID, text))


def main(args):
    nlp = spacy.load(args.lang)
    docs = [nlp(line) for line in tqdm(list(gen_lines(args.text)), desc="Tokenizing " + args.text, unit=" lines")]
    docs = [(doc, {t.orth_ for t in doc}) for doc in docs]
    out = open(args.out, "w", encoding="utf-8", newline="") if args.out else sys.stdout
    writer = csv.writer(out, delimiter="\t")
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
