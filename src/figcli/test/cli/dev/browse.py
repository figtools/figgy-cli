import sys
import time

import pexpect
from figcli.test.cli.test_utils import TestUtils

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.get import GetAction
from figcli.test.cli.actions.put import PutAction
from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.utils.utils import *

KEY_UP = 'k'
KEY_DOWN = 'j'
KEY_PATH = '/shared/aaa/aa'


class DevBrowse(FiggyTest):

    def __init__(self, extra_args="", key_down_to_shared=1):
        super().__init__(None, extra_args=extra_args)
        self.key_down_to_shared = key_down_to_shared

    def run(self):
        self.step("Prepping browse")
        self._setup()
        self.step("Sleeping for 45 to ensure the cache gets populated with the new /shared value")
        time.sleep(45)
        self.step(f"Testing browse for {param_1}")
        self.browse()
        self.step("Cleaning up")
        self._cleanup()

    def _cleanup(self):
        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(KEY_PATH, delete_another=False)

    def _setup(self):
        put = PutAction(extra_args=self.extra_args)
        put.add(KEY_PATH, DELETE_ME_VALUE, param_1_desc, add_more=False, delete_first=False)

    def _validate_delete(self, key, value):
        print(f"Validating successfully deletion of {key}")
        get = GetAction(extra_args=self.extra_args)
        get.get(key, value, get_more=False, expect_missing=True)
        print("Delete success validated.")

    ## Get through browse, then delete
    def browse(self):
        print(f"Getting {KEY_PATH} through browse...")
        # Get Value
        child = TestUtils.spawn(f'{CLI_NAME} config {browse.name} --env {DEFAULT_ENV} '
                              f'--skip-upgrade {self.extra_args}')
        time.sleep(5) ## let browse start

        for i in range(0, self.key_down_to_shared):
            child.send(KEY_DOWN)
            time.sleep(.25)

        child.send('e')
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
        child.send('e')
        child.send(KEY_DOWN)
        child.send('s')
        child.sendcontrol('n')  # <-- sends TAB
        child.sendcontrol('m')  # <-- Sends ENTER
        child.expect(f'.*{DELETE_ME_VALUE}.*')

        self.step("Get success. Deleting through browse.")
        # Delete Value
        child = TestUtils.spawn(f'{CLI_NAME} config {browse.name} --env {DEFAULT_ENV} '
                                f'--skip-upgrade {self.extra_args}')
        time.sleep(5) ## let browse start

        for i in range(0, self.key_down_to_shared):
            child.send(KEY_DOWN)
            time.sleep(.25)

        child.send('e')
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
        child.send('e')
        child.send(KEY_DOWN)
        child.send('d')
        child.sendcontrol('n')  # <-- sends TAB
        child.sendcontrol('m')  # <-- Sends ENTER
        child.expect(f'.*{KEY_PATH}.*')
        child.sendline('y')
        child.expect(f'.*{KEY_PATH}.*deleted successfully.*')

        self.step("Delete success!")
        self._validate_delete(KEY_PATH, DELETE_ME_VALUE)
