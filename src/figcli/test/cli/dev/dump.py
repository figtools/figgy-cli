import pexpect
import sys

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.put import PutAction
from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.test.cli.test_utils import TestUtils
from figcli.utils.utils import *
import time


class DevDump(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)

    def run(self):
        put = PutAction(extra_args=self.extra_args)

        # Use a number > 10 so paging is tested
        minimum, maximum = 1, 12
        put.add(param_1, param_1_val, param_1_desc, add_more=True, delete_first=False)

        for i in range(minimum, maximum):
            more = i < maximum - 1
            put.add_another(f'{param_1}-{i}', param_1_val, f'{param_1_desc}-{i}', add_more=more)

        child = TestUtils.spawn(f'{CLI_NAME} config {dump.name} --env {DEFAULT_ENV} {self.extra_args}'
                              f' --skip-upgrade')

        self.step(f"Testing `{CLI_NAME} config {dump.name} --env {DEFAULT_ENV}`")
        child.expect('.*to dump from.*')
        child.sendline(dump_prefix)
        child.expect(f'.*{param_1}-{minimum}.*{param_1}-{maximum-1}.*')
        print(f"Dump was successful.")

        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(param_1, delete_another=True, check_delete=False)
        for i in range(minimum, maximum):
            delete.delete(f'{param_1}-{i}', delete_another=i < maximum - 1)
