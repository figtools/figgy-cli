import pexpect

from figcli.test.cli.action import FiggyAction
from figcli.test.cli.config import *
from figcli.utils.utils import *


class GetAction(FiggyAction):
    def __init__(self, extra_args=""):
        super().__init__(pexpect.spawn(f'{CLI_NAME} config {Utils.get_first(get)} --env {DEFAULT_ENV} '
                                       f'--skip-upgrade {extra_args}',
                                       timeout=10, encoding='utf-8'), extra_args=extra_args)

    def get(self, key, value, get_more=False, expect_missing=False, no_decrypt=False, retry=True):
        response = self.expect(['.*PS Name.*', pexpect.TIMEOUT])

        if response == 1 and retry:
            self.alert(f"Received timeout, PERFORMING RETRY for KEY: {key}")
            self.get(key, value, get_more=get_more, expect_missing=expect_missing, retry=False)
        else:
            self.sendline(key)
            if expect_missing:
                self.expect(f'.*Invalid PS Name specified.*')
                print("Missing parameter validated.")
            elif no_decrypt:
                self.expect(f'.*do not have access.*')
                print("Lack of decrypt permissions validated.")
            else:
                self.expect(f'.*{value}.*Get another.*')
                print(f"Expected value of {value} validated.")
            if get_more:
                print("Getting another")
                self.sendline('y')
            else:
                print("Not getting another")
                self.sendline('n')
