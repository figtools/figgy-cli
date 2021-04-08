import pexpect
from figcli.test.cli.config import *
from figcli.test.cli.dev.get import *
from figcli.test.cli.figgy import FiggyTest
from figcli.config import *
from figcli.utils.utils import *


class DataDelete(FiggyTest):
    def __init__(self, extra_args=""):
        print(f"Testing `{CLI_NAME} config {delete.name} --env {DEFAULT_ENV}`")
        super().__init__(pexpect.spawn(f'{CLI_NAME} config {delete.name} --env {DEFAULT_ENV}'
                                       f' --skip-upgrade {extra_args}',
                                    timeout=20, encoding='utf-8'), extra_args=extra_args)

    def run(self):
        self.step(f"Testing delete for param: {param_1}")
        self.delete(param_1)

    def delete(self, name, delete_another=False, repl_source_delete=False, repl_dest_delete=False, retry=True):
        self.expect('.*PS Name.*')
        self.sendline(name)
        print(f"Delete sent for {name}")
        result = self.expect_multiple([".*You may NOT delete sources that are actively replicating.*", 
                                      f".*active replication destination.*{name}.*", 
                                      ".*deleted successfully.*",
                                      pexpect.TIMEOUT])
        print(f"Match: {result}")

        if result == 0:
            if repl_source_delete:
                print("VALIDATING REPL_SOURCE_DELETE")
                Utils.stc_validate(repl_source_delete, "Encountered REPL Source delete but that was not expected!!")

        if result == 1:
            if repl_dest_delete:
                print("VALIDATING REPL_DEST_DELETE")
                Utils.stc_validate(repl_dest_delete, "Encountered REPL Dest delete but that was not expected!!")

            self.sendline('y')
            self.expect(f".*{name}.*deleted successfully.*Delete another.*")

            if delete_another:
                self.sendline('y')
            else:
                self.sendline('n')

        if result == 2:
            print("Validating delete success.")
            get = DevGet(extra_args=self.extra_args)
            get.get(param_1, param_1_val, expect_missing=True)

            if delete_another:
                self.sendline('y')
            else:
                self.sendline('n')
                
        elif result == 3 and retry:
            self.step("EXECUTING RETRY, RECEIVED TIMEOUT!!")
            retry = DataDelete(extra_args=self.extra_args)
            retry.delete(name, retry=False)

        print("Successful delete validated.")
