import pexpect
from figcli.test.cli.config import *
from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.put import PutAction
from figcli.test.cli.figgy import FiggyTest
from figcli.config import *
from figcli.utils.utils import *


class DevGet(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(pexpect.spawn(f'{CLI_NAME} config {get.name} --env {DEFAULT_ENV} '
                                       f'--skip-upgrade {extra_args}',
                                       timeout=20, encoding='utf-8'), extra_args=extra_args)

    def run(self):
        self.step(f"Preparing get by adding: {param_1}")
        put = PutAction(extra_args=self.extra_args)
        put.add(param_1, param_1_val, param_1_desc, add_more=False)

        self.step(f"Testing GET for {param_1}")
        self.get(param_1, param_1_val, get_more=False)

        self.step(f"Cleaning up: {param_1}")
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(param_1, check_delete=True, delete_another=False)

    def get(self, key, value, get_more=False, expect_missing=False, no_decrypt=False):
        self.expect('.*PS Name.*')
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