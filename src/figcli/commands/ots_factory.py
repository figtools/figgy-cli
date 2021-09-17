from boto3.session import Session

from figcli.commands.factory import Factory
from figcli.commands.one_time_secret.get import Get
from figcli.commands.one_time_secret.put import Put
from figcli.commands.ots_context import OTSContext
from figcli.svcs.one_time_secret import OTSService
from figcli.utils.utils import *


class OTSFactory(Factory):
    def __init__(self, command: frozenset,
                 context: OTSContext,
                 env_session: Session,
                 colors_enabled: bool,
                 ots_svc: OTSService,
                 all_sessions: Optional[Dict[str, Session]] = None):

        self._all_sessions: Optional[Dict[str, Session]] = all_sessions
        self._command = command
        self._utils = Utils(colors_enabled)
        self._ots_context: OTSContext = context
        self._env_session: Session = env_session
        self._ots_svc = ots_svc
        self._colors_enabled = colors_enabled

    def instance(self):
        return self.get(self._command)

    def get(self, command: frozenset):
        if command == ots_get:
            return Get(self._ots_svc, self._ots_context, self._colors_enabled)
        elif command == ots_put:
            return Put(self._ots_svc, self._ots_context, self._colors_enabled)
        else:
            self._utils.error_exit(f"{command} is not a valid 'ots' command. You must select from: "
                                   f"[{CollectionUtils.printable_set(ots_commands)}]. Try using --help for more info.")
