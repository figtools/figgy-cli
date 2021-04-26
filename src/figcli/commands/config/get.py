from typing import Tuple, Optional

from botocore.exceptions import ClientError
from prompt_toolkit.completion import WordCompleter

from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figgy.data.dao.ssm import SsmDao
from figcli.io.input import Input
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import *


class Get(ConfigCommand):

    def __init__(self, ssm_init: SsmDao, config_completer_init: WordCompleter,
                 colors_enabled: bool, config_context: ConfigContext):
        super().__init__(get, colors_enabled, config_context)
        self._ssm = ssm_init
        self._config_completer = config_completer_init
        self._utils = Utils(colors_enabled)
        self._out = Output(colors_enabled)

    def get_val_and_desc(self, key: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            return self.get_param_and_desc(key)
        except ClientError as e:
            denied = "AccessDeniedException" == e.response['Error']['Code']
            if denied and "AWSKMS; Status Code: 400;" in e.response['Error']['Message']:
                self._out.error(f"\nYou do not have access to decrypt the value of: [[{key}]]")
            elif denied:
                self._out.error(f"\nYou do not have access to Parameter: [{key}]]")
            else:
                raise
        return None, None

    def get_param_and_desc(self, key: str) -> Tuple[Optional[str], Optional[str]]:
        return self._ssm.get_parameter_with_description(key)

    def get(self, key: str) -> Optional[str]:
        return self._ssm.get_parameter(key)

    def _get_param(self):
        get_another = True

        while get_another:
            key = Input.input(f"PS Name: ", completer=self._config_completer)
            if key:
                value, desc = self.get_val_and_desc(key)
                if value:
                    self._out.print(f"[[Value:]] {value}")
                    desc = desc if desc else DESC_MISSING_TEXT
                    self._out.print(f"[[Description:]] {desc}")
                else:
                    self._out.error(f"Invalid PS Name specified.")
                get_another = Input.y_n_input(f"\nGet another?", default_yes=False, invalid_no=True)
                print()

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self._get_param()
