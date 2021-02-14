import pexpect

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.utils.utils import *
import sys



class DevPut(FiggyTest):
    def __init__(self, extra_args=""):
        print(f"Testing `figgy config {put.name} --env {DEFAULT_ENV}`")
        super().__init__(pexpect.spawn(f'{CLI_NAME} config {put.name} '
                                       f'--env {DEFAULT_ENV} --skip-upgrade {extra_args}', timeout=45, encoding='utf-8'),
                                       extra_args=extra_args)

    def run(self):
        self.step(f"Testing PUT for {param_1}")
        self.add(param_1, param_1_val, param_1_desc)
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(param_1, check_delete=True)

    def add(self, key, value, desc, delete_first=True, add_more=False):
        if delete_first:
            delete = DeleteAction(extra_args=self.extra_args)
            delete.delete(key)

        self.expect('.*Please input a PS Name.*')
        self.sendline(key)
        self.expect('.*Please input a value.*')
        self.sendline(value)
        self.expect('.*Please input an optional.*')
        self.sendline(desc)
        self.expect('.*secret?.*')
        self.sendline('n')
        self.expect('.*another.*')
        if add_more:
            self.sendline('y')
        else:
            self.sendline('n')

    def add_encrypt_app(self, key, value, desc, add_more=False):
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(key)
        self.expect('.*Please input a PS Name.*')
        self.sendline(key)
        self.expect('.*Please input a value.*')
        self.sendline(value)
        self.expect('.*Please input an optional.*')
        self.sendline(desc)
        self.expect('.*secret?.*')
        self.sendline('y')
        index = self.expect(['.*key.*', '.*another.*'])
        if index == 0:
            self.sendline('app')
            self.expect('.*another.*')

        if add_more:
            self.sendline('y')
        else:
            self.sendline('n')

    def add_another(self, key, value, desc, add_more=True):
        print(f"Adding another: {key} -> {value}")
        self.expect('.*PS Name.*')
        self.sendline(key)
        self.expect('.*Please input a value.*')
        self.sendline(value)
        self.expect('.*Please input an optional.*')
        self.sendline(desc)
        self.expect('.*secret?.*')
        self.sendline('n')
        self.expect('.*Add another.*')
        if add_more:
            self.sendline('y')
        else:
            self.sendline('n')
