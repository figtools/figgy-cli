import sys

import pexpect

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.get import GetAction

from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.test.cli.test_utils import TestUtils
from figcli.utils.utils import *


class DataSync(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)

    def run(self):
        self.step("Prepping workspace, deleting any existing values.")
        self.prep()

        child = TestUtils.spawn(f'{CLI_NAME} {config.name} {sync.name} '
                              f'--env {DEFAULT_ENV} --config figcli/test/assets/data_repl_conf.json '
                              f'--skip-upgrade --replication-only {self.extra_args}', timeout=30)
        time.sleep(2)
        with open('figcli/test/assets/data_repl_conf.json', 'r') as file:
            content = json.loads(file.read()).get('replicate_figs')

        self.step("Running replication-only sync and adding values.")
        sources = list(content.keys())
        for source in sources:
            child.expect(f".*input a value.*")
            child.sendline(DELETE_ME_VALUE)
            child.expect(".*description.*")
            child.sendline("desc")
            child.expect(".*secret.*")
            child.sendline('y')
            child.expect('.*encryption.*')
            child.sendline('data')
            child.expect('.*added successfully.*')

        self.step("Waiting for replication propagation")
        time.sleep(50)

        self.step("Verifying successful replication")
        destinations = list(content.values())
        for dest in destinations:
            GetAction().get(dest, DELETE_ME_VALUE, get_more=False, no_decrypt=True)

        self.step("Cleaning leftover values")
        self.prep()

    def prep(self):
        with open('figcli/test/assets/data_repl_conf.json', 'r') as file:
            content = json.loads(file.read()).get('replicate_figs')

        delete = DeleteAction()
        destinations = list(content.values())
        for i in range(0, len(destinations)):
            print(f"DELETING: {destinations[i]}")

            if i < len(destinations):
                delete.delete(destinations[i], delete_another=True)
            else:
                delete.delete(destinations[i], delete_another=False)

        delete = DeleteAction()
        sources = list(content.keys())
        print(f"SOURCES: {sources}")
        for i in range(0, len(sources)):
            print(f"DELETING: {destinations[i]}")
            if i < len(sources):
                delete.delete(sources[i], delete_another=True)
            else:
                delete.delete(sources[i], delete_another=False)
