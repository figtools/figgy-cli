import pexpect
from figcli.test.cli.action import FiggyAction

from figcli.test.cli.config import *
from figcli.test.cli.actions.get import GetAction
from figcli.utils.utils import *


class DeleteAction(FiggyAction):
    def __init__(self, extra_args=""):
        print(f"Testing `figgy config {Utils.get_first(delete)} --env {DEFAULT_ENV}`")
        super().__init__(
            pexpect.spawn(f'{CLI_NAME} config {Utils.get_first(delete)} --env {DEFAULT_ENV} '
                          f'{extra_args} --skip-upgrade',
                          timeout=20, encoding='utf-8'), extra_args=extra_args)

    def delete(self, name, check_delete=False, delete_another=False, retry=True):
        result = self.expect(['.*PS Name to Delete.*', pexpect.TIMEOUT])

        if result == 1 and retry:
            self.alert("EXECUTING RETRY, RECEIVED TIMEOUT!!")
            retry = DeleteAction(extra_args=self.extra_args)
            retry.delete(name, retry=False)
        else:
            self.sendline(name)
            print(f"Delete sent for {name}")
            result = self.expect(['.*deleted successfully.*Delete another.*', '.*SOURCE.*',
                                  '.*ALSO delete this replication config.*', pexpect.TIMEOUT])

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
            elif result == 3 and retry:
                self.alert("EXECUTING RETRY, RECEIVED TIMEOUT!!")
                retry = DeleteAction(extra_args=self.extra_args)
                retry.delete(name, retry=False)