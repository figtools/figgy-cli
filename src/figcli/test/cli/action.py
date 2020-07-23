from typing import Union, List

import pexpect

from figcli.utils.utils import Utils
import sys


class FiggyAction:
    """
    Actions prevent cyclic dependencies, and are designed for leveraging FiggyCli for cleanup steps when running inside
    of tests.
    """

    def __init__(self, command, extra_args=""):
        self.c = Utils.default_colors()
        self.command = command
        self.extra_args = extra_args
        self._child = self.spawn(command)
        print(f"{self.c.fg_yl}Executing action: {self._child.args}{self.c.rs}")
        self._child.logfile = sys.stdout
        self._child.delaybeforesend = .5

    def spawn(self, command: str):
        return pexpect.spawn(command, timeout=10, encoding='utf-8')

    def expect_multiple(self, regexes: List[str]):
        print(f'Expecting: {regexes}')
        return self._child.expect(regexes)

    def expect(self, regex: Union[List[str], str], retry=True):
        print(f'Expecting: {regex}')
        expect_list = [regex] + [pexpect.TIMEOUT] if isinstance(regex, str) else regex + [pexpect.TIMEOUT]
        result = self._child.expect(expect_list)
        if result == len(expect_list) - 1 and retry:
            self.alert(f"EXPECT FAILED: {regex} initiating retry!")
            self._child = self.spawn(self.command)
            return self.expect(regex, retry=False)
        else:
            return result

    def sendline(self, line: str):
        print(f'Sending: {line}')
        self._child.sendline(line)

    def wait(self):
        self._child.wait()

    def alert(self, msg: str):
        print(f"{self.c.fg_yl}-----------------------------------------{self.c.rs}")
        print(f"{self.c.fg_rd} ALERT: {msg}{self.c.rs}")
        print(f"{self.c.fg_yl}-----------------------------------------{self.c.rs}")