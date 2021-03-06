import pexpect
from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.test.cli.dev.put import DevPut
from figcli.test.cli.dev.get import DevGet
from figcli.test.cli.dev.delete import DevDelete
from figcli.config import *
from figcli.utils.utils import *
import time

KEY_UP = 'k'
KEY_DOWN = 'j'
KEY_PATH = '/shared/aaa/aa'


class DevOpsBrowse(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)

    def run(self):
        self.step(f"Testing browse for {param_1}")
        self.browse()

    def _cleanup(self):
        delete = DevDelete(extra_args=self.extra_args)
        delete.delete(KEY_PATH, delete_another=False)

    def _setup(self):
        put = DevPut(extra_args=self.extra_args)
        put.add(KEY_PATH, DELETE_ME_VALUE, param_1_desc, add_more=False)

    def _validate_delete(self, key, value):
        print(f"Validating successfully deletion of {key}")
        get = DevGet(extra_args=self.extra_args)
        get.get(key, value, get_more=False, expect_missing=True)
        print("Delete success validated.")

    ## Get through browse, then delete
    def browse(self):
        self._setup()
        self.step("Sleeping for 15 to ensure the cache gets populated with the new /shared value")
        time.sleep(15)
        print(f"Getting {KEY_PATH} through browse...")
        # Get Value
        child = pexpect.spawn(f'{CLI_NAME} config {browse.name} --env {DEFAULT_ENV} '
                              f'--skip-upgrade {self.extra_args}',
                              timeout=20, encoding='utf-8')
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
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
        child = pexpect.spawn(f'{CLI_NAME} config {browse.name} --env {DEFAULT_ENV} '
                              f'--skip-upgrade {self.extra_args}',
                              timeout=20, encoding='utf-8')
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
        child.send(KEY_DOWN)
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