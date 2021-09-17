from figgy.data.dao.audit import AuditDao
from prompt_toolkit.completion import WordCompleter

from figcli.config.commands import audit
from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figgy.data.dao.ssm import SsmDao
from figcli.io.input import Input
from figcli.io.output import Output
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import Utils


class Audit(ConfigCommand):
    """
    Returns audit history for a queried PS Name
    """
    def __init__(self, ssm_init: SsmDao, audit_init: AuditDao, config_completer_init: WordCompleter,
                 colors_enabled: bool, config_context: ConfigContext):
        super().__init__(audit, colors_enabled, config_context)
        self._ssm = ssm_init
        self._audit_dao = audit_init
        self._config_completer = config_completer_init
        self._utils = Utils(colors_enabled)
        self._out = Output(colors_enabled)

    def _audit(self):
        audit_more = True

        while audit_more:
            ps_name = Input.input(f"Please input a PS Name : ", completer=self._config_completer)
            audit_logs = self._audit_dao.get_audit_logs(ps_name)
            result_count = len(audit_logs)
            if result_count > 0:
                self._out.print(f"\nFound [[{result_count}]] results.")
            else:
                self._out.warn(f"\nNo results found for: [[{ps_name}]]")
            for log in audit_logs:
                self._out.print(log.pretty_print())

            to_continue = input(f"Audit another? (Y/n): ")
            to_continue = to_continue if to_continue != '' else 'y'
            audit_more = to_continue.lower() == "y"
            print()

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self._audit()
