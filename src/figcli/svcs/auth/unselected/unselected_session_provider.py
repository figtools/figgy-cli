from typing import Optional

import boto3

from figcli.commands.figgy_context import FiggyContext
from figcli.models.defaults.defaults import CLIDefaults
from figcli.svcs.auth.provider.session_provider import SessionProvider
from figcli.ui.models.global_environment import GlobalEnvironment


class UnselectedSessionProvider(SessionProvider):
    """
    Always throws a NotImplementedError when called, but does not break bootstrapping for some particular use cases, such as when
    `--version` is provided on an unconfigured figgy.
    """

    def __init__(self, defaults: CLIDefaults, context: FiggyContext):
        super().__init__(defaults, context)

    def get_session(self, env: GlobalEnvironment, prompt: bool, exit_on_fail=True, mfa: Optional[str] = None) -> boto3.Session:
        raise NotImplementedError("You have not selected a provider, please run `figgy --configure` first.")

    def cleanup_session_cache(self):
        pass
