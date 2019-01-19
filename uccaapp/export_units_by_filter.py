import argparse
from ucca import layer1, convert
from uccaapp.download_task import TaskDownloader

desc = "Get all units according to a specified filter. Units that meet any of the filters are output."

CONSECUTIVE = "CONSECUTIVE"
SUBSEQUENCE = "SUBSEQUENCE"
SUBSET = "SUBSET"


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


def tokens_match(tokens1, tokens2, mode):
    """
    Returns True iff tokens2 is contained in tokens1.
    mode can be CONSECUTIVE, SUBSET, SUBSEQUENCE
    :param tokens1:
    :param tokens2:
    :param mode:
    """
    if mode == SUBSET:
        return set(tokens2).issubset(set(tokens1))
    else:
        try:
            indices = [tokens1.index(t) for t in tokens2]
            if mode == CONSECUTIVE:
                return indices == list(range(indices[0],indices[0]+len(indices)))
            elif mode == SUBSEQUENCE:
                return indices == sorted(indices)
            else:
                raise Exception("Invalid option for token mode")
        except ValueError:
            return False


def main(output = None, comment = False, sentence_level = False, categories = (), tokens = (), tokens_mode = CONSECUTIVE,
         case_insensitive = False, write = False, **kwargs):
    filtered_nodes = []
    for passage, task_id, user_id in TaskDownloader(**kwargs).download_tasks(write=False, **kwargs):
        if sentence_level:
            cur_passages = convert.split2sentences(passage)
            all_nodes = [P.layer('1').heads[0] for P in cur_passages]
        else:
            all_nodes = list(passage.layer(layer1.LAYER_ID).all)
        for node in all_nodes:
            if comment and node.extra.get("remarks"):
                filtered_nodes.append(("comment",node,task_id,user_id))
            if tokens and not node.attrib.get("implicit"):
                unit_tokens = [t.text for t in node.get_terminals(punct=True)]
                if case_insensitive:
                    unit_tokens = [x.lower() for x in unit_tokens]
                    tokens = [x.lower() for x in tokens]
                if tokens_match(unit_tokens, tokens, tokens_mode):
                    filtered_nodes.append(('TOKENS', node, task_id, user_id))
            else:
                all_tags = []
                for edge in node:
                    all_tags.extend([c.tag for c in edge.categories])
                if all_tags:
                    intersection = set(categories) & set(all_tags)
                    if intersection:
                        filtered_nodes.append((str(list(intersection)), node, task_id, user_id))

    if output:
        with open(output, 'w') as f:
            for filter_type,node,task_id,user_id in filtered_nodes:
                ancestor = get_top_level_ancestor(node)
                print(filter_type, task_id, user_id, node.extra.get("tree_id"), node.to_text(),
                      ancestor, str(node.extra.get("remarks")).replace("\n","|"), file=f, sep="\t")


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskDownloader.add_arguments(argument_parser)
    argument_parser.add_argument("--output", help="output file name")
    argument_parser.add_argument("--categories", nargs="+", default=(), help="Abbreviations of the names of the categories to filter by")
    argument_parser.add_argument("--tokens", nargs="+", default=(),
                                 help="Tokens to filter by")
    argument_parser.add_argument("--tokens-mode", default=CONSECUTIVE,
                                 help="mode of search for the tokens: CONSECUTIVE,SUBSEQUENCE,SUBSET")
    argument_parser.add_argument("--sentence-level", action="store_true",
                                 help="output sentences rather than units")
    argument_parser.add_argument("--case-insensitive", action="store_true",
                                 help="make tokens search case insensitive")
    argument_parser.add_argument("--comment", action="store_true", help="Output all the units that have comments")

    main(**vars(argument_parser.parse_args()))
