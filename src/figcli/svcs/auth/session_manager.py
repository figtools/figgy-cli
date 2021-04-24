import logging
from typing import Optional

import boto3

from figcli.models.defaults.defaults import CLIDefaults
from figcli.svcs.auth.provider.session_provider import SessionProvider
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class SessionManager:
    _MAX_ATTEMPTS = 5

    def __init__(self, defaults: CLIDefaults, session_provider: SessionProvider):
        self._sts = boto3.client('sts')
        self._utils = Utils(defaults.colors_enabled)
        self._defaults = defaults
        self.session_provider: SessionProvider = session_provider

    @Utils.trace
    def get_session(self, env: GlobalEnvironment, prompt: bool, exit_on_fail=True,
                    mfa: Optional[str] = None) -> boto3.Session:
        """
        Creates a session in the specified ENV for the target role from a SAML assertion returned by SSO authentication.
        Args:
            assumable_role: AssumableRole - The role to be leveraged to authenticate this session
            prompt: If prompt is set, we will not use a cached session and will generate new sessions for okta and mgmt.
            exit_on_fail: Exit the program if this session hydration fails.

        returns: Hydrated session for role + account that match the specified one in the provided AssumableRole
        """
        return self.session_provider.get_session(env, prompt, exit_on_fail=exit_on_fail, mfa=mfa)
