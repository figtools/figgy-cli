import sys
import time

import pexpect

from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.utils.utils import *


class DevOTS(FiggyTest):
    SECRET_VALUE_1 = 'test-secret-1'
    SECRET_VALUE_2 = 'test-secret-2'
    SECRET_VALUE_3 = 'test-secret-3'
    EXPIRATION_WAIT_PERIOD = 120

    def __init__(self, extra_args=""):
        print(f"Testing `figgy ots {ots_put.name}")
        super().__init__(None, extra_args=extra_args)

    def __child_get(self):
        child = pexpect.spawn(f'figgy ots {ots_get.name} '
                                    f'--skip-upgrade {self.extra_args}', timeout=45, encoding='utf-8')
        self.__init_child(child)
        return child

    def __child_put(self):
        child = pexpect.spawn(f'figgy ots {ots_put.name} '
                      f'--skip-upgrade {self.extra_args}', timeout=45, encoding='utf-8')
        self.__init_child(child)
        return child

    def __init_child(self, child):
        c = Utils.default_colors()
        print(f"{c.fg_yl}Testing command: {child.args}{c.rs}")
        child.logfile = sys.stdout
        child.delaybeforesend = .5

    def run(self):
        self.step(f"Testing PUT for {param_1}")
        expiring_child = self.__child_put()
        expiring_id: str = self.put(expiring_child, self.SECRET_VALUE_3, .02)

        first_child = self.__child_put()
        first_id: str = self.put(first_child, self.SECRET_VALUE_1, 1)

        second_child = self.__child_put()
        second_id: str = self.put(second_child, self.SECRET_VALUE_2, .01)

        child = self.__child_get()
        self.get(child, first_id, self.SECRET_VALUE_1)

        child = self.__child_get()
        self.get(child, second_id, self.SECRET_VALUE_2)

        child = self.__child_get()
        self.get(child, first_id, None)

        # Disabling expiration test for now, it appears that expirtation is delayed by AWS. Not sure the interval.
        # print(f"Waiting for {self.EXPIRATION_WAIT_PERIOD} seconds for parameter to auto-expire")
        # time.sleep(self.EXPIRATION_WAIT_PERIOD)
        #
        # child = self.__child_get()
        # self.get(child, expiring_id, None)

    def put(self, child, secret_value: str, expires) -> str:
        child.expect('.*Please input a value.*')
        child.sendline(secret_value)
        child.expect('.*auto-expires.*')
        child.sendcontrol('u')  # deletes the auto-inputted text
        child.sendline(str(expires))
        output = self.readline(count=20, child=child)
        secret_id = re.search(r'.*Secret Id.* -> ([\w+-]+)', output, flags=re.MULTILINE).group(1)
        self.log(f'Parsed secret: {secret_id}')
        return secret_id

    def get(self, child, lookup_key: str, expected_value: Optional[str]):
        child.expect('.*Please input.*')
        child.sendline(lookup_key)
        if expected_value:
            child.expect(f'.*{expected_value}.*')
        else:
            child.expect('.*does not exist.*')
