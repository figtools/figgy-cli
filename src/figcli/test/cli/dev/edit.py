import pexpect
from figcli.test.cli.test_utils import TestUtils

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.get import GetAction
from figcli.test.cli.actions.put import PutAction
from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.utils.utils import *


#Todo get this working...
class DevEdit(FiggyTest):
    _VALUE = 'asdf'
    _DESC = 'desc'

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)

    def run(self):
        self.step(f"Testing edit for {param_1}")
        self.edit()

    def prep(self):
        put = PutAction(extra_args=self.extra_args)
        put.add(param_1, param_1_val, param_1_desc, delete_first=False)

    def edit(self):
        # Get Value
        child = TestUtils.spawn(f'{CLI_NAME} config {edit.name} --env {DEFAULT_ENV} '
                              f'--skip-upgrade {self.extra_args}')

        child.expect('.*Please input a PS Name.*')
        child.sendline(param_1)
        time.sleep(12)  # Give edit time to start
        child.send(DevEdit._VALUE)
        child.sendcontrol('n')  # <-- sends TAB
        child.send(DevEdit._DESC)
        child.sendcontrol('n')  # <-- sends TAB
        child.sendcontrol('m')  # <-- Sends ENTER
        child.expect('.*secret.*')
        child.sendline('n')
        child.expect('.*saved successfully.*')
        print("Add success. Checking successful save")

        get = GetAction(extra_args=self.extra_args)
        get.get(param_1, DevEdit._VALUE, DevEdit._DESC)
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(param_1)
