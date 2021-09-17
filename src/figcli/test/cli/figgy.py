from abc import ABC, abstractmethod
from typing import List, Union

from pexpect.exceptions import TIMEOUT
from figcli.utils.utils import Utils
import sys


class FiggyTest(ABC):

    def __init__(self, child, extra_args=""):
        self.c = Utils.default_colors()
        self.extra_args = extra_args

        if child:
            c = Utils.default_colors()
            print(f"{c.fg_yl}Testing command: {child.args}{c.rs}")
            self._child = child
            self._child.logfile = sys.stdout
            self._child.delaybeforesend = .5

    @abstractmethod
    def run(self):
        pass

    def log(self, text: str):
        with open('/tmp/figgy.log', "a+") as l:
            l.writelines([text])


    def expect_multiple(self, regexes: List[str]):
        print(f'Expecting: {regexes}')
        return self._child.expect(regexes)

    def expect(self, regex: Union[List[str], str]):
        print(f'Expecting: {regex}')
        return self._child.expect(regex)

    def sendline(self, line: str):
        print(f'Sending: {line}')
        self._child.sendline(line)

    def step(self, step_msg: str):
        print(f"{self.c.fg_bl}-----------------------------------------{self.c.rs}")
        print(f"{self.c.fg_yl} STEP: {step_msg}{self.c.rs}")
        print(f"{self.c.fg_bl}-----------------------------------------{self.c.rs}")

    def wait(self):
        print("Waiting for child process to exit...")
        self._child.wait()

    def readline(self, count=1, child=None):
        data = ""
        for i in range(0, count):
            if child:
                data += child.readline()
            else:
                data += self.readline()

        return data

    def sendcontrol(self, characters: str):
        return self._child.sendcontrol(characters)