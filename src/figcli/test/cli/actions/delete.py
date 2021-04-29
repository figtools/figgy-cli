import pexpect
from figcli.test.cli.action import FiggyAction

from figcli.test.cli.config import *
from figcli.test.cli.actions.get import GetAction
from figcli.utils.utils import *


class DeleteAction(FiggyAction):
    def __init__(self, extra_args=""):
        print(f"Testing `figgy config {delete.name} --env {DEFAULT_ENV}`")
        super().__init__(f'{CLI_NAME} config {delete.name} --env {DEFAULT_ENV} '
                         f'{extra_args} --skip-upgrade', extra_args=extra_args)

    def delete(self, name, check_delete=False, delete_another=False):
        self.expect('.*PS Name to Delete.*')
        self.sendline(name)
        print(f"Delete sent for {name}")
        result = self.expect(['.*deleted successfully.*Delete another.*', '.*SOURCE.*',
                              '.*ALSO delete this replication config.*'])

        if result == 0:
            if check_delete:
                get = GetAction(extra_args=self.extra_args)
                get.get(name, DELETE_ME_VALUE, expect_missing=True)

            if delete_another:
                self.sendline('y')
            else:
                self.sendline('n')

            print("Successful delete validated.")
        elif result == 2:
            self.sendline('y')
            self.expect('.*deleted successfully.*')

            if delete_another:
                self.sendline('y')
            else:
                self.sendline('n')