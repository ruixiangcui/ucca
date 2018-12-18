import argparse
import sys

from ucca import layer1
from uccaapp.download_task import TaskDownloader

desc = "Get all units according to a specified filter. Units that meet any of the filters are output."

def get_top_level_ancestor(node):
    """
    Traverses the passage upwards until a root node is reached
    :param node:
    :return:
    """
    parent = node
    while parent.fparent:
        parent = parent.fparent
    return parent

def isIntersecting(L1,L2):
    return set(L1) & set(L2)

def main(comment = False, categories = (), **kwargs):
    filtered_nodes = []
    for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(**kwargs, write=False):
        for node in passage.layer(layer1.LAYER_ID).all:
            if comment and node.extra.get("remarks"):
                filtered_nodes.append(("comment",node))
            else:
                all_tags = node.extra.get("all_tags")
                if all_tags:
                    intersection = set(categories) & set(node.extra.get("all_tags").split(';'))
                    if intersection:
                        filtered_nodes.append((str(list(intersection)),node))

    for filter_type,node in filtered_nodes:
        ancestor = get_top_level_ancestor(node)
        print('\t'.join([filter_type,str(task_id),str(user_id),node.extra.get("tree_id"),node.to_text(),str(ancestor),str(node.extra.get("remarks"))]))

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    argument_parser.add_argument("--categories", nargs="+", help="Abbreviations of the names of the categories to filter by")
    argument_parser.add_argument("--comment", action="store_true", help="Output all the units that have comments")

    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
