import argparse
import string
from glob import glob

from tqdm import tqdm

from ucca import core, layer0, layer1
from ucca.ioutil import write_passage

PUNCTUATION = set(string.punctuation)


def gen_lines(patterns):
    for pattern in patterns:
        for filename in glob(pattern) or [pattern]:
            with open(filename, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield line


def main(args):
    for i, line in enumerate(tqdm(gen_lines(args.filenames), unit=" lines", desc="Creating passages"), start=1):
        p = core.Passage(args.format % i)
        l0 = layer0.Layer0(p)
        layer1.Layer1(p)
        for tok in line.split():
            l0.add_terminal(text=tok, punct=PUNCTUATION.issuperset(tok))
        write_passage(p, outdir=args.out_dir, binary=args.binary, verbose=False)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Create unannotated passage files from tokenized and split text")
    argparser.add_argument("filenames", nargs="+", help="Input filenames containing tokenized and sentence-split text")
    argparser.add_argument("-o", "--out-dir", help="Directory to write output files to")
    argparser.add_argument("-f", "--format", default="1%04d0", help="String format for passage IDs")
    argparser.add_argument("-b", "--binary", action="store_true", help="Write Pickle files instead of XML")
    main(argparser.parse_args())
