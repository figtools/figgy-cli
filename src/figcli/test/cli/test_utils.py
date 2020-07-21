import sys

import pexpect


class TestUtils:
    @staticmethod
    def spawn(command: str):
        child = pexpect.spawn(command, encoding='utf-8', timeout=20)
        child.logfile = sys.stdout
        child.delaybeforesend = .5
        return child

    @staticmethod
    def spawn_no_log(command: str):
        child = pexpect.spawn(command, encoding='utf-8', timeout=20)
        child.delaybeforesend = .5
        return child