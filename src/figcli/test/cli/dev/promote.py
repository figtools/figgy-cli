from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.put import PutAction
from figcli.test.cli.config import *

from figcli.test.cli.figgy import FiggyTest
from figcli.test.cli.test_utils import TestUtils
from figcli.utils.utils import *


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
        put = PutAction(extra_args=self.extra_args)
        put.add('/app/test-promote/v1/config9', DELETE_ME_VALUE, desc='desc', add_more=True)
        put.add('/app/test-promote/v1/config11', DELETE_ME_VALUE, desc='desc', add_more=True)
        put.add('/app/test-promote/v1/config12', DELETE_ME_VALUE, desc='desc', add_more=True)
        put.add_encrypt_app('/app/test-promote/v1/config13', DELETE_ME_VALUE, desc='desc', add_more=False)

    def promote(self):
        print(f"Testing: {CLI_NAME} config {promote.name} --env {DEFAULT_ENV} "
              f"--config figcli/test/assets/success/figgy.json")
        child = TestUtils.spawn(f'{CLI_NAME} config {promote.name} --env {DEFAULT_ENV} '
                                f'--skip-upgrade {self.extra_args}')
        child.expect(f'.*prefix to promote.*')
        child.sendline('/app/test-promote/')
        child.expect('.*destination environment.*')
        if DEFAULT_ENV == 'qa':
            child.sendline('stage')
        else:
            child.sendline('qa')

        child.expect('.*promote.*config11.*')
        child.sendline('y')
        child.expect('.*promote.*config12.*')
        child.sendline('n')
        child.expect('.*Skipping param.*config13.*promote.*9.*')
        child.sendline('y')
        child.expect(".*Success.*")

    def prune(self):
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete('/app/test-promote/v1/config9', delete_another=True, check_delete=False)
        delete.delete('/app/test-promote/v1/config11', delete_another=True, check_delete=False)
        delete.delete('/app/test-promote/v1/config12', delete_another=True, check_delete=False)
        delete.delete('/app/test-promote/v1/config13', delete_another=False, check_delete=False)
