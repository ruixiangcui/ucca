import argparse
import os
import sys
import urllib.request

from ucca import layer1, convert
from uccaapp.download_task import TaskDownloader

desc = "Get all units according to a specified filter. Units that meet any of the filters are output."

CONSECUTIVE = "CONSECUTIVE"
SUBSEQUENCE = "SUBSEQUENCE"
SUBSET = "SUBSET"


def read_amr_roles(role_type):
    file_name = "have-" + role_type + "-role-91-roles-v1.06.txt"
    if not os.path.exists(file_name):
        url = r"http://amr.isi.edu/download/lists/" + file_name
        try:
            urllib.request.urlretrieve(url, file_name)
        except OSError as e:
            raise IOError("Must download %s and have it in the current directory when running the script" % url) from e
    with open(file_name) as f:
        return [line.split()[1] for line in map(str.strip, f) if line and not line.startswith(("#", "MAYBE"))]


AMR_ROLE = {role for role_type in ("org", "rel") for role in read_amr_roles(role_type)}
TOKEN_CLASSES = {
    "[ROLE]": AMR_ROLE
}


def get_top_level_ancestor(node):
    """
    Traverses the passage upwards until a unit which is immediately below the root is reached
    :param node:
    :return:
    """
    # if node is already the root, return it
    if not node.fparent:
        return node
    parent = node
    while parent.fparent.fparent:
        parent = parent.fparent
    return parent


def tokens_match(tokens1, tokens2, mode):
    """
    Returns True iff tokens2 is contained in tokens1.
    mode can be CONSECUTIVE, SUBSET, SUBSEQUENCE
    :param tokens1:
    :param tokens2:
    :param mode:
    """
    if mode == SUBSET:
        return set(tokens2).issubset(tokens1)
    try:
        indices = [tokens1.index(t) for t in tokens2]
        if mode == CONSECUTIVE:
            return indices == list(range(indices[0], indices[0] + len(indices)))
        elif mode == SUBSEQUENCE:
            return indices == sorted(indices)
    except ValueError:
        return False
    raise ValueError("Invalid option for token mode: " + mode)


def main(output=None, comment=False, sentence_level=False, categories=(), tokens=(), tokens_mode=CONSECUTIVE,
         case_insensitive=False, write=False, **kwargs):
    expanded_tokens = []
    for token in tokens:
        expanded = TOKEN_CLASSES.get(token)
        if expanded:
            expanded_tokens.extend(expanded)
        else:
            expanded_tokens.append(token)
    tokens = expanded_tokens

    filtered_nodes = []
    for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(write=False, **kwargs):
        if sentence_level:
            cur_passages = convert.split2sentences(passage)
            all_nodes = [p.layer(layer1.LAYER_ID).heads[0] for p in cur_passages]
        else:
            all_nodes = list(passage.layer(layer1.LAYER_ID).all)
        for node in all_nodes:
            if comment and node.extra.get("remarks"):
                filtered_nodes.append(("comment", node, task_id, user_id))
            if tokens and not node.attrib.get("implicit"):
                unit_tokens = [t.text for t in node.get_terminals(punct=True)]
                if case_insensitive:
                    unit_tokens = [x.lower() for x in unit_tokens]
                    tokens = [x.lower() for x in tokens]
                if tokens_match(unit_tokens, tokens, tokens_mode):
                    filtered_nodes.append(('TOKENS', node, task_id, user_id))
            else:
                all_tags = [c.tag for edge in node for c in edge.categories]
                intersection = set(categories).intersection(all_tags)
                if intersection:
                    filtered_nodes.append((str(intersection), node, task_id, user_id))
    f = open(output, 'w', encoding="utf-8") if output else sys.stdout
    for filter_type, node, task_id, user_id in filtered_nodes:
        ancestor = get_top_level_ancestor(node)
        print(filter_type, task_id, user_id, node.extra.get("tree_id"), node.to_text(),
              ancestor, str(node.extra.get("remarks")).replace("\n", "|"), file=f, sep="\t")
    if output:
        f.close()


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    argument_parser.add_argument("--output", help="output file name")
    argument_parser.add_argument("--categories", nargs="+", default=(),
                                 help="Abbreviations of the names of the categories to filter by")
    argument_parser.add_argument("--tokens", nargs="+", default=(),
                                 help="Tokens to filter by")
    argument_parser.add_argument("--tokens-mode", default=CONSECUTIVE, choices=(CONSECUTIVE, SUBSEQUENCE, SUBSET),
                                 help="mode of search for the tokens")
    argument_parser.add_argument("--sentence-level", action="store_true",
                                 help="output sentences rather than units")
    argument_parser.add_argument("--case-insensitive", action="store_true",
                                 help="make tokens search case insensitive")
    argument_parser.add_argument("--comment", action="store_true", help="Output all the units that have comments")

    main(**vars(argument_parser.parse_args()))
