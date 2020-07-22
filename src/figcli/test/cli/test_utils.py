import sys

import pexpect


class TestUtils:
    @staticmethod
    def spawn(command: str, timeout=45):
        child = pexpect.spawn(command, encoding='utf-8', timeout=timeout)
        child.logfile = sys.stdout
        child.delaybeforesend = .5
        return child

    @staticmethod
    def spawn_no_log(command: str, timeout=45):
        child = pexpect.spawn(command, encoding='utf-8', timeout=timeout)
        child.delaybeforesend = .5
        return child