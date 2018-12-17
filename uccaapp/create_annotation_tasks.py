#!/usr/bin/env python3
import sys

import argparse

from uccaapp.api import ServerAccessor

desc = """Convert a passage file to JSON format and upload to UCCA-App as a completed task"""


class AnnotationTaskCreator(ServerAccessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def create_annotation_task(self, filename, review=False, manager_comment=None, **kwargs):
        del kwargs
        with open(filename) as f:
            num = 0
            for line in f:
                fields = line.strip().split()
                if len(fields) != 2:
                    sys.stderr.write("Error in line: "+line.strip())
                    continue
                user_id = fields[0]
                user_model = self.get_user(user_id)
                task_id = fields[1]
                task_out = self.get_task(task_id)
                assert task_out["type"] in (["ANNOTATION", "REVIEW"] if review else ["TOKENIZATION"]), \
                    "Wrong input task given: %s for task ID %s" % (task_out["type"], task_id)
                task_in = dict(type="REVIEW" if review else "ANNOTATION", status="NOT_STARTED",
                               project=task_out["project"], user=user_model,
                               passage=task_out["passage"], manager_comment=manager_comment or "",
                               user_comment="", parent=task_out,
                               is_demo=False, is_active=True)
                self.create_task(**task_in)
                num += 1
            print("Uploaded %d tasks successfully." % num, file=sys.stderr)

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename", help="a file where each line is a <User ID> <INPUT TASK ID>, "
                                                "where the input task may be an annotation/review task "
                                                "(if given --review) or a tokenization task")
        ServerAccessor.add_arguments(argparser)
        argparser.add_argument("-r", "--review", action="store_true", help="Create annotation/review task")
        argparser.add_argument("--manager-comment", action="store_true", help="Manager comment to set for all tasks")


def main(**kwargs):
    AnnotationTaskCreator(**kwargs).create_annotation_task(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    AnnotationTaskCreator.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
