from typing import Union, List

from figcli.utils.utils import Utils
import sys


class FiggyAction:
    """
    Actions prevent cyclic dependencies, and are designed for leveraging FiggyCli for cleanup steps when running inside
    of tests.
    """

    def __init__(self, child, extra_args=""):
        self.c = Utils.default_colors()
        self.extra_args = extra_args

        if child:
            c = Utils.default_colors()
            print(f"{c.fg_yl}Executing action: {child.args}{c.rs}")
            self._child = child
            self._child.logfile = sys.stdout
            # self._child.delayafterread = .1
            self._child.delaybeforesend = .5

    def expect_multiple(self, regexes: List[str]):
        print(f'Expecting: {regexes}')
        return self._child.expect(regexes)

    def expect(self, regex: Union[List[str], str]):
        print(f'Expecting: {regex}')
        return self._child.expect(regex)

    def sendline(self, line: str):
        print(f'Sending: {line}')
        self._child.sendline(line)

    def wait(self):
        self._child.wait()
