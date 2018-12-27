#!/usr/bin/env python3
import sys

import argparse

from ucca.convert import from_json
from ucca.ioutil import write_passage
from uccaapp.api import ServerAccessor

desc = """Download task from UCCA-App and convert to a passage in standard format"""


class TaskDownloader(ServerAccessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def download_tasks(self, task_ids, by_filename=False, **kwargs):
        if by_filename:
            task_ids_from_file = []
            for filename in task_ids:
                with open(filename,'r') as f:
                    task_ids_from_file.extend([x.strip() for x in f])
            task_ids = task_ids_from_file
        for task_id in task_ids:
            yield self.download_task(task_id, **kwargs)

    def download_task(self, task_id, write=True, binary=None, out_dir=None, prefix=None, **kwargs):
        del kwargs
        task_json = self.get_user_task(task_id)
        user_id = task_json["user"]["id"]
        passage = from_json(task_json)
        if write:
            write_passage(passage, binary=binary, outdir=out_dir, prefix=prefix)
        return passage, task_id, user_id

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("task_ids", nargs="+", help="IDs of tasks to download and convert")
        argparser.add_argument("-f","--by-filename",
                               action="store_true",help="if true, task_ids is a filename, if false, it is a list of IDs")
        TaskDownloader.add_write_arguments(argparser)
        ServerAccessor.add_arguments(argparser)

    @staticmethod
    def add_write_arguments(argparser):
        argparser.add_argument("-o", "--out-dir", default=".", help="output directory")
        argparser.add_argument("-p", "--prefix", default="", help="output filename prefix")
        argparser.add_argument("-b", "--binary", action="store_true", help="write in binary format (.pickle)")


def main(**kwargs):
    list(TaskDownloader(**kwargs).download_tasks(**kwargs))


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
