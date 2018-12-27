import argparse
import sys

from ucca import layer1
from uccaapp.download_task import TaskDownloader

desc = "Get all units according to a specified filter. Units that meet any of the filters are output."

def get_top_level_ancestor(node):
    """
    Traverses the passage upwards until a unit which is immediately below the root is reached
    :param node:
    :return:
    """
    # if node is already the root, return it
    if not node.fparent:
        return node
    else:
        parent = node
        while parent.fparent.fparent:
            parent = parent.fparent
        return parent

def main(output = None, comment = False, categories = (), **kwargs):
    filtered_nodes = []
    for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(**kwargs, write=False):
        for node in passage.layer(layer1.LAYER_ID).all:
            if comment and node.extra.get("remarks"):
                filtered_nodes.append(("comment",node,task_id,user_id))
            else:
                all_tags = node.extra.get("all_tags")
                if all_tags:
                    intersection = set(categories) & set(all_tags.split(';'))
                    if intersection:
                        filtered_nodes.append((str(list(intersection)),node,task_id,user_id))

    if output:
        f = open(output,'w')
        for filter_type,node,task_id,user_id in filtered_nodes:
            ancestor = get_top_level_ancestor(node)
            f.write('\t'.join([filter_type,str(task_id),str(user_id),node.extra.get("tree_id"),node.to_text(),
                               str(ancestor),str(node.extra.get("remarks")).replace("\n","|")])+'\n')
        f.close()

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    argument_parser.add_argument("--output",
                                 help="output file name")
    argument_parser.add_argument("--categories", nargs="+", default=(), help="Abbreviations of the names of the categories to filter by")
    argument_parser.add_argument("--comment", action="store_true", help="Output all the units that have comments")

    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
