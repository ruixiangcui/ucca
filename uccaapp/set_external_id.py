#!/usr/bin/env python3
import sys

import argparse
from tqdm import tqdm

from uccaapp.api import ServerAccessor

desc = """Set the external ID for passages"""


class ExternalIdSetter(ServerAccessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_external_ids(self, filename, **kwargs):
        del kwargs
        with open(filename, encoding="utf-8") as f:
            passage_id_to_external_id = list(map(str.split, map(str.strip, f)))
        for external_id, passage_id in tqdm(passage_id_to_external_id, unit=" passages", desc="Setting external IDs"):
            passage = self.get_passage(passage_id)
            passage["external_id"] = external_id
            passage_out = self.update_passage(**passage)
            assert passage_out["external_id"] == external_id, "External ID failed to update for passage %s" % passage_id
            yield passage_out

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename", help="file with lines of the form <EXTERNAL ID> <PASSAGE ID>")
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    list(ExternalIdSetter(**kwargs).set_external_ids(**kwargs))


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    ExternalIdSetter.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
