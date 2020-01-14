import argparse
import os
import sys
import urllib.request
from itertools import product

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


def tokens_match(unit_tokens, query_tokens, mode):
    """
    :param unit_tokens: candidate unit tokens, as a list of strings
    :param query_tokens: list of lists of tokens to look for, each list representing alternatives for a position
    :param mode: CONSECUTIVE, SUBSET, SUBSEQUENCE
    :return whether query_tokens is contained in unit_tokens
    """
    if mode == SUBSET:
        return any(set(query).issubset(unit_tokens) for query in product(*query_tokens))
    indices = []
    for alternatives in query_tokens:
        index = None
        for alternative in alternatives:
            try:
                index = unit_tokens.index(alternative)
            except ValueError:
                pass
        if index is None:
            return False
        indices.append(index)
    if mode == CONSECUTIVE:
        return indices == list(range(indices[0], indices[-1] + 1))
    elif mode == SUBSEQUENCE:
        return indices == sorted(indices)
    raise ValueError("Invalid option for token mode: " + mode)


## def main(output = None, comment = False, sentence_level = False, categories = (), tokens = (), tokens_mode = CONSECUTIVE,
##          case_insensitive = False, tokens_by_file = False, remotes = False, write = False, **kwargs):
##     if tokens_by_file:
##         with open(tokens[0]) as f:
##             token_lists = [line.strip().split() for line in f]
##     elif tokens != ():
##         token_lists = [tokens]
##     else:
##         token_lists = ()

##     filtered_nodes = []
##     for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(write=False, **kwargs):
##         if sentence_level:
##             cur_passages = convert.split2sentences(passage)
##             all_nodes = [p.layer(layer1.LAYER_ID).heads[0] for p in cur_passages]
##         else:
##             all_nodes = list(passage.layer(layer1.LAYER_ID).all)
##         for node in all_nodes:
##             if comment and node.extra.get("remarks"):
##                 filtered_nodes.append(("comment",node,task_id,user_id))
##             if remotes and len([n for n in node.outgoing if n.attrib.get("remote")]) > 0:
##                 filtered_nodes.append(("remotes", node, task_id, user_id))
##             if token_lists and not node.attrib.get("implicit"):
##                 for token_list in token_lists:
##                     unit_tokens = [t.text for t in node.get_terminals(punct=True)]
##                     if case_insensitive:
##                         unit_tokens = [x.lower() for x in unit_tokens]
##                         token_list = [x.lower() for x in token_list]
##                     if tokens_match(unit_tokens, token_list, tokens_mode):
##                         filtered_nodes.append(('TOKENS', node, task_id, user_id))
##             else:
##                 all_tags = [c.tag for edge in node for c in edge.categories]
##                 intersection = set(categories).intersection(all_tags)

def filter_nodes(categories=(), tokens=(), tokens_mode=CONSECUTIVE, case_insensitive=False, comment=False,
                 sentence_level=False, remotes=False, **kwargs):
    for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(**kwargs):
        for node in [p.layer(layer1.LAYER_ID).heads[0] for p in convert.split2sentences(passage)] if sentence_level \
                else passage.layer(layer1.LAYER_ID).all:
            if comment and node.extra.get("remarks"):
                yield "comment", node, task_id, user_id
            if remotes:
                if node.attrib.get("implicit"):
                    yield 'IMPLICIT', node, task_id, user_id
                for e in node.incoming:
                    if e.attrib.get("remote"):
                        yield 'REMOTE', e.parent, task_id, user_id
            if tokens and not node.attrib.get("implicit"):
                unit_tokens = [t.text for t in node.get_terminals(punct=True)]
                if case_insensitive:
                    unit_tokens = [x.lower() for x in unit_tokens]
                    tokens = [x.lower() for x in tokens]
                if tokens_match(unit_tokens, tokens, tokens_mode):
                    yield 'TOKENS', node, task_id, user_id
            elif categories:
                intersection = set(categories).intersection(c.tag for e in node for c in e.categories)
                if intersection:
                    yield str(intersection), node, task_id, user_id


def main(output=None, tokens=(), **kwargs):
    kwargs["write"] = False
    f = open(output, 'w', encoding="utf-8") if output else sys.stdout
    expanded_tokens = [TOKEN_CLASSES.get(token, [token]) for token in tokens]
    for filter_type, node, task_id, user_id in filter_nodes(tokens=expanded_tokens, **kwargs):
        ancestor = get_top_level_ancestor(node)
        print(filter_type, task_id, user_id, node.extra.get("tree_id"), node.to_text(),
              ancestor, str(node.extra.get("remarks")).replace("\n", "|"), file=f, sep="\t", flush=True)
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
    argument_parser.add_argument("--tokens-by-file", action="store_true",
                                 help="tokens will be specified in a file instead of in the command line. Each line consists of space delimited list of tokens.")
    argument_parser.add_argument("--tokens-mode", default=CONSECUTIVE,
                                 help="mode of search for the tokens: CONSECUTIVE,SUBSEQUENCE,SUBSET")
    argument_parser.add_argument("--sentence-level", action="store_true",
                                 help="output sentences rather than units")
    argument_parser.add_argument("--case-insensitive", action="store_true",
                                 help="make tokens search case insensitive")
    argument_parser.add_argument("--comment", action="store_true", help="Output all the units that have comments")
    argument_parser.add_argument("--remotes", action="store_true", help="Output all the units that have remote children")

    main(**vars(argument_parser.parse_args()))

