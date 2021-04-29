import sys
import time
import pexpect
from figcli.test.cli.test_utils import TestUtils

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.config import *
from figcli.test.cli.dev.sync import DevSync
from figcli.test.cli.figgy import FiggyTest
from figcli.utils.utils import *


class DevValidate(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)
        self.missing_key = '/app/ci-test/v1/config12'

    def run(self):
        self.step("Testing successful validate.")
        self.validate_success()
        self.step("Testing validate with errors")
        self.validate_error()

    def validate_success(self):
        sync = DevSync(extra_args=self.extra_args)
        sync.prep_sync()
        sync.sync_success()
        print("Sleeping to give time for replication")
        time.sleep(50)

        print(f"Testing: {CLI_NAME} config {validate.name} --env {DEFAULT_ENV} "
              f"--config figcli/test/assets/success/figgy.json {self.extra_args}")
        child = TestUtils.spawn(f'{CLI_NAME} config {validate.name} --env {DEFAULT_ENV} '
                              f'--config figcli/test/assets/success/figgy.json --skip-upgrade {self.extra_args}')
        child.expect(".*Success.*")
        print("VALIDATE SUCCESS VERIFIED")

    def validate_error(self):
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(self.missing_key)
        print(f"Testing: {CLI_NAME} config {validate.name} --env {DEFAULT_ENV} "
              f"--config figcli/test/assets/error/figgy.json {self.extra_args}")
        child = TestUtils.spawn(f'{CLI_NAME} config {validate.name} --env {DEFAULT_ENV} '
                              f'--config figcli/test/assets/error/figgy.json --skip-upgrade {self.extra_args}')
        child.expect('.*missing at least one.*')
        print("VALIDATE ERROR VERIFIED")
