import pexpect
from figcli.test.cli.config import *
from figcli.test.cli.actions.get import GetAction
from figcli.test.cli.figgy import FiggyTest
from figcli.config import *
from figcli.utils.utils import *


class DevDelete(FiggyTest):
    def __init__(self, extra_args=""):
        print(f"Testing `figgy config {Utils.get_first(delete)} --env {DEFAULT_ENV}`")
        super().__init__(
            pexpect.spawn(f'{CLI_NAME} config {Utils.get_first(delete)} --env {DEFAULT_ENV} '
                          f'{extra_args} --skip-upgrade',
                          timeout=20, encoding='utf-8'), extra_args=extra_args)

    def run(self):
        print(f"Testing DELETE for {param_1}")
        self.delete(param_1, check_delete=True)

    def delete(self, name, check_delete=False, delete_another=False):
        self.expect('.*PS Name to Delete.*')
        self.sendline(name)
        print(f"Delete sent for {name}")
        result = self.expect(['.*deleted successfully.*Delete another.*', '.*SOURCE.*'])

        if result == 0:
            if check_delete:
                get = GetAction(extra_args=self.extra_args)
                get.get(name, DELETE_ME_VALUE, expect_missing=True)

            if delete_another:
                self.sendline('y')
            else:
                self.sendline('n')

            print("Successful delete validated.")
