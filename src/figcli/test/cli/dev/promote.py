import sys

import pexpect
from figcli.test.cli.config import *
from figcli.test.cli.dev.get import DevGet
from figcli.test.cli.dev.delete import DevDelete
from figcli.test.cli.dev.put import DevPut

from figcli.test.cli.figgy import FiggyTest
from figcli.config import *
from figcli.utils.utils import *
import uuid
import time


class DevPromote(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)
        self.missing_key = '/app/ci-test/v1/config12'

    def run(self):
        self.step("Preparing promote process...")
        self.prep_promote()
        self.step("Testing successful promote")
        self.promote()

    def prep_promote(self):
        put = DevPut(extra_args=self.extra_args)
        put.add('/app/test-promote/v1/config9', DELETE_ME_VALUE, desc='desc', add_more=True)
        put.add('/app/test-promote/v1/config11', DELETE_ME_VALUE, desc='desc', add_more=True)
        put.add('/app/test-promote/v1/config12', DELETE_ME_VALUE, desc='desc', add_more=True)
        put.add_encrypt_app('/app/test-promote/v1/config13', DELETE_ME_VALUE, desc='desc', add_more=False)

    def promote(self):
        print(f"Testing: {CLI_NAME} config {Utils.get_first(promote)} --env {DEFAULT_ENV} "
              f"--config figcli/test/assets/success/figgy.json")
        child = pexpect.spawn(f'{CLI_NAME} config {Utils.get_first(promote)} --env {DEFAULT_ENV} '
                              f'--skip-upgrade {self.extra_args}',
                              encoding='utf-8', timeout=20)
        child.logfile = sys.stdout
        child.expect(f'.*prefix to promote.*')
        child.sendline('/app/test-promote/')
        child.expect('.*destination environment.*')
        child.sendline('qa')
        child.expect('.*promote.*config11.*')
        child.sendline('y')
        child.expect('.*promote.*config12.*')
        child.sendline('n')
        child.expect('.*Skipping param.*config13.*promote.*9.*')
        child.sendline('y')

    def prune(self):
        delete = DevDelete(extra_args=self.extra_args)
        delete.delete('/app/test-promote/v1/config9', delete_another=True)
        delete.delete('/app/test-promote/v1/config11', delete_another=True)
        delete.delete('/app/test-promote/v1/config12', delete_another=True)
        delete.delete('/app/test-promote/v1/config13', delete_another=False)
