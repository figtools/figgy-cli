import pexpect
from figcli.test.cli.config import *
from figcli.test.cli.figgy import FiggyTest
from figcli.utils.utils import *
import os


class ConfigureGoogle(FiggyTest):
    def __init__(self, role_type: str):
        self._role_type = role_type
        super().__init__(None)

        # super().__init__(pexpect.spawn(f'{CLI_NAME} --{configure.name} --skip-upgrade {self.extra_args}',
        #                       encoding='utf-8', timeout=20))
        self._child = pexpect.spawn(f'{CLI_NAME} --{configure.name} --skip-upgrade {self.extra_args}',
                              encoding='utf-8', timeout=20)

    def run(self):
        self.step(f"Testing `{CLI_NAME} --{configure.name}`")
        user_name = os.environ.get(GOOGLE_SSO_USER)
        password = os.environ.get(GOOGLE_SSO_PASSWORD)
        idp_id = os.environ.get(GOOGLE_IDP_ID)
        sp_id = os.environ.get(GOOGLE_SP_ID)
        mfa_secret = os.environ.get(GOOGLE_MFA_SECRET)

        self._child.expect('.*select.*GOOGLE.*')
        self._child.sendline('GOOGLE')
        self._child.expect('.*GOOGLE username.*')
        self._child.sendline(user_name)
        self._child.expect('.*GOOGLE password.*')
        self._child.sendline(password)
        self._child.expect('.*mfa_enabled.*')
        self._child.sendline('n')
        self._child.expect('.*Use Multi-factor.*')
        self._child.sendline('y')
        self._child.expect('.*auto_mfa.*')
        self._child.sendline('n')
        self._child.expect('.*Would you.*generate.*')
        self._child.sendline('y')
        self._child.expect('.*auto-generate.*')
        self._child.sendline(mfa_secret)
        self._child.expect('.*Google Account.*')
        self._child.sendline(idp_id)
        self._child.expect('.*Please input.*Provider ID.*')
        self._child.sendline(sp_id)
        selected = self._child.expect(['.*overwrite.*REDACTED.*', '.*Choose MFA.*'])
        if selected == 1:
            self._child.sendline("2")
            self._child.expect('.*')

        self._child.sendline(self._role_type)
        self._child.expect('.*Options.*dev.*')
        self._child.sendline('dev')
        self._child.expect('.*region.*')
        self._child.sendline('y')
        self._child.expect('.*weirdness.*')
        self._child.sendline('n')
        self._child.expect('.*overwrite.*')
        self._child.expect('.*Setup successful.*', timeout=50)
        self.step(f"GOOGLE with role: {self._role_type} configured successfully")
