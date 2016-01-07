import re

from ucca.layer1 import EdgeTags

from config import Config


class Action(object):
    type_to_id = {}
    all_actions = None
    all_action_ids = None

    RIGHT = 0
    LEFT = 1

    def __init__(self, action_type, tag=None, orig_edge=None, orig_node=None, oracle=None):
        self.type = action_type  # String
        self.tag = tag  # Usually the tag of the created edge; but if COMPOUND_SWAP, the distance
        self.orig_node = orig_node  # Node created by this action, if any (during training)
        self.orig_edge = orig_edge
        self.edge = None  # Will be set by State when the edge created by this action is known
        self.oracle = oracle

        self.type_id = Action.type_to_id.get(self.type)  # Allocate ID for fast comparison
        if self.type_id is None:
            self.type_id = len(Action.type_to_id)
            Action.type_to_id[self.type] = self.type_id
        self._id = None

    def is_type(self, *others):
        return self.type_id in (o.type_id for o in others)

    def apply(self):
        if self.oracle is not None:
            self.oracle.remove(self.orig_edge, self.orig_node)

    @staticmethod
    def from_string(s):
        m = re.match("(.*)-(.*)", s)
        if m:  # String contains tag
            action_type, tag = m.groups()
            return Action(action_type, tag)
        return Action(s)

    @classmethod
    def edge_action(cls, direction, remote, tag, *args, **kwargs):
        if direction == cls.RIGHT:
            return Actions.RightRemote(tag, *args, **kwargs) if remote else Actions.RightEdge(tag, *args, **kwargs)
        else:
            return Actions.LeftRemote(tag, *args, **kwargs) if remote else Actions.LeftEdge(tag, *args, **kwargs)

    def __repr__(self):
        return Action.__name__ + "(" + self.type + (", " + self.tag if self.tag else "") + ")"

    def __str__(self):
        return self.type + ("-" + str(self.tag) if self.tag else "")

    def __eq__(self, other):
        return self.id == other.id

    def __call__(self, *args, **kwargs):
        return Action(self.type, *args, **kwargs)

    @property
    def remote(self):
        return self.is_type(Actions.LeftRemote, Actions.RightRemote)

    @property
    def id(self):
        if self._id is None:
            Action.get_all_actions()
            self._id = Action.all_action_ids[(self.type_id, self.tag)]
        return self._id

    @classmethod
    def get_all_actions(cls):
        if cls.all_actions is None:
            cls.all_actions = [action(tag) for action in
                               (Actions.Node, Actions.Implicit,
                                Actions.LeftEdge, Actions.RightEdge,
                                Actions.LeftRemote, Actions.RightRemote)
                               for name, tag in EdgeTags.__dict__.items()
                               if isinstance(tag, str) and not name.startswith('__')] + \
                              [Actions.Reduce, Actions.Shift, Actions.Finish]
            if Config().compound_swap:
                cls.all_actions.extend(Actions.Swap(i) for i in range(1, Config().max_swap + 1))
            else:
                cls.all_actions.append(Actions.Swap)
            cls.all_action_ids = {(action.type_id, action.tag): i
                                  for i, action in enumerate(cls.all_actions)}
        return cls.all_actions

    @classmethod
    def by_id(cls, i):
        return cls.get_all_actions()[i]


class Actions:
    Shift = Action("SHIFT")
    Node = Action("NODE")
    Implicit = Action("IMPLICIT")
    Reduce = Action("REDUCE")
    LeftEdge = Action("LEFT-EDGE")
    RightEdge = Action("RIGHT-EDGE")
    LeftRemote = Action("LEFT-REMOTE")
    RightRemote = Action("RIGHT-REMOTE")
    Swap = Action("SWAP")
    Finish = Action("FINISH")
