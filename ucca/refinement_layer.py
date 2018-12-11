"""Describes a refinement layer.

a refinement layer for UCCA's Foundational layer, it is used to refine a specific relation in
the parent layer

"""


from ucca import core, layer1

LAYER_ID = '2' # TODO: extend this to generate id based on the parent id

class RefinementNode(core.Node):
    """
    a refinement node is...
    """
    def __init__(self, foundational_node):
        n = foundational_node.ID.split(core.Node.ID_SEPARATOR)[-1]
        id = "{}{}{}".format(LAYER_ID, core.Node.ID_SEPARATOR, n)
        super().__init__(root = self.root, tag = "", ID = id, attrib = {})


class RefinementLayer(core.Layer):
    """

    """

    def __init__(self, root, attrib=None, *, orderkey=core.id_orderkey):
        super().__init__(ID=LAYER_ID, root=root, attrib=attrib,
                         orderkey=orderkey)
        self._all = []

    def add_node(self, parent, edge_tag, child):
        """Adds a new :class:`FNode` whose parent and Edge tag are given.

        :param parent: the FNode which will be the parent of the new RNode.
                If the parent is None, adds under the layer head FNode.
        :param edge_tag: the tag on the Edge between the parent and the new FNode.

        :return: the newly created RNode

        :raise core.FrozenPassageError if the Passage is frozen
        """
        rnode = RefinementNode(child)
        parent.add(edge_tag, rnode)
        return rnode


    def _add_edge(self, edge):
        super()._add_edge(edge)
        self._update_edge(edge)

    def _remove_edge(self, edge):
        super()._remove_edge(edge)
        self._update_edge(edge)

    def _change_edge_tag(self, edge, old_tag):
        super()._change_edge_tag(edge, old_tag)
        self._update_edge(edge)
