import time
import uuid

from figcli.test.cli.actions.delete import DeleteAction
from figcli.test.cli.actions.get import GetAction
from figcli.test.cli.actions.put import PutAction
from figcli.test.cli.config import *
from figcli.test.cli.dev.audit import DevAudit
from figcli.test.cli.figgy import FiggyTest
from figcli.test.cli.test_utils import TestUtils
from figcli.utils.utils import *

RESTORE_PROPAGATION_TIME = 120


class DevRestore(FiggyTest):

    def __init__(self, extra_args=""):
        super().__init__(None, extra_args=extra_args)
        self._guuid = uuid.uuid4().hex
        print(f"Guuid generated: {self._guuid}")

    def run(self):
        minimum, maximum = 1, 3
        first_val = 'FIRST_VAL'
        second_val = 'SECOND_VAL'
        self.step("Adding new configs. To Restore")
        self._setup(minimum, maximum, value_override=first_val)
        print("Waiting for propagation...")
        time.sleep(RESTORE_PROPAGATION_TIME)
        print("Validating")
        self._audit(minimum, maximum)
        restore_breakpoint_1 = int(time.time() * 1000)
        print(f"First restore breakpoint: {restore_breakpoint_1} - would expect val of {first_val}")

        time.sleep(15)
        self._setup(minimum, maximum, value_override=second_val)
        print("Waiting for propagation...")
        time.sleep(RESTORE_PROPAGATION_TIME)
        print("Validating")
        self._audit(minimum, maximum)
        restore_breakpoint_2 = int(time.time() * 1000)
        print(f"Second restore breakpoint: {restore_breakpoint_1} - would expect val of {second_val}")

        time.sleep(25)

        restore_prefix = f'{param_test_prefix}{self._guuid}/'
        self.step(f"Attempting restore to time: {restore_breakpoint_1} with prefix: {restore_prefix}")
        child = TestUtils.spawn(f'{CLI_NAME} config {restore.name} --env {DEFAULT_ENV} --skip-upgrade'
                              f' --point-in-time {self.extra_args}')
        child.expect('.*Which.*recursively restore.*')
        child.sendline(restore_prefix)
        child.expect('.*Seconds.*restore.*')
        child.sendline(f'{restore_breakpoint_1}')
        child.expect('.*Are you sure.*')
        child.sendline('y')
        print("Checking restore output...\r\n\r\n")
        child.expect(f'.*Value.*{param_test_prefix}{self._guuid}/test_param.*')
        child.expect(f'.*restored successfully!.*')  ## <-- this is needed or else the child proccess exits too early

        time.sleep(5)
        self.step("Validating values were rolled back... Part 1")

        get = GetAction(extra_args=self.extra_args)
        get.get(f'{param_test_prefix}{self._guuid}/test_param', first_val, get_more=True)
        for i in range(minimum, maximum):
            get.get(f'{param_test_prefix}{self._guuid}/test_param-{i}', first_val, get_more=i < maximum - 1)

        print("Values were rolled back successfully")
        time.sleep(30)
        print("Testing restore to second restore point")

        restore_prefix = f'{param_test_prefix}{self._guuid}/'
        self.step(f"Attempting restore to time: {restore_breakpoint_2} with prefix: {restore_prefix}")
        child = TestUtils.spawn(f'{CLI_NAME} config {restore.name} --env {DEFAULT_ENV} --skip-upgrade'
                                f' --point-in-time {self.extra_args}')
        child.expect('.*Which.*recursively restore.*')
        child.sendline(restore_prefix)
        child.expect('.*Seconds.*restore.*')
        child.sendline(f'{restore_breakpoint_2}')
        child.expect('.*Are you sure.*')
        child.sendline('y')
        print("Checking restore output...\r\n\r\n")
        child.expect(f'.*Restoring.*{param_test_prefix}{self._guuid}/test_param.*{second_val}.*')
        child.expect(f'.*restored successfully!.*')  ## <-- this is needed or else the child proccess exits too early

        time.sleep(5)
        self.step("Validating values were rolled back... Part 2")

        get = GetAction(extra_args=self.extra_args)
        get.get(f'{param_test_prefix}{self._guuid}/test_param', second_val, get_more=True)
        for i in range(minimum, maximum):
            get.get(f'{param_test_prefix}{self._guuid}/test_param-{i}', second_val, get_more=i < maximum - 1)

        print("Values were rolled forward successfully. Cleaning up...")

        delete = DeleteAction(extra_args=self.extra_args)
        delete.delete(f'{param_test_prefix}{self._guuid}/test_param', delete_another=True)
        for i in range(minimum, maximum):
            delete.delete(f'{param_test_prefix}{self._guuid}/test_param-{i}', delete_another=i < maximum - 1)

    def _setup(self, min: int, max: int, value_override: str = None):
        # Do not want to do a delete -> Put b/c it will mess up the restore, so delete_first=False is required.
        put = PutAction(extra_args=self.extra_args)
        value = value_override if value_override else DELETE_ME_VALUE
        put.add(f'{param_test_prefix}{self._guuid}/test_param', value, param_1_desc,
                add_more=True, delete_first=False)

        for i in range(min, max):
            put.add_another(f'{param_test_prefix}{self._guuid}/test_param-{i}', value, f'{param_1_desc}-{i}',
                            add_more=i < max - 1)

        get = GetAction(extra_args=self.extra_args)
        get.get(f'{param_test_prefix}{self._guuid}/test_param', value, get_more=True)
        for i in range(min, max):
            get.get(f'{param_test_prefix}{self._guuid}/test_param-{i}', value, get_more=i < max - 1)

    def _audit(self, min: int, max: int):
        audit = DevAudit(extra_args=self.extra_args)
        audit.audit(f'{param_test_prefix}{self._guuid}/test_param', audit_another=True)

        for i in range(min, max):
            audit.audit(f'{param_test_prefix}{self._guuid}/test_param-{i}', audit_another=i < max - 1)
