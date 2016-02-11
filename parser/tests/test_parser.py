"""Testing code for the parser package, unit-testing only."""

import unittest

from ucca import convert
from ucca.tests.test_ucca import TestUtil
from state import State
from oracle import Oracle


class ParserTests(unittest.TestCase):
    def test_oracle(self):
        passage = convert.from_standard(TestUtil.load_xml('test_files/standard3.xml'))
        oracle = Oracle(passage)
        state = State(passage, passage.ID)
        actions_taken = []
        while True:
            actions = oracle.get_actions(state)
            action = next(iter(actions))
            state.transition(action)
            actions_taken.append("%s\n" % action)
            if state.finished:
                break
        with open('test_files/standard3.oracle_actions.txt') as f:
            self.assertSequenceEqual(actions_taken, f.readlines())
