from typing import List

from botocore.exceptions import ClientError
from figgy.data.dao.replication import ReplicationDao
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from figcli.config.style.style import FIGGY_STYLE
from figcli.config.commands import *
from figcli.io.input import Input
from figcli.io.output import Output
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import Utils
from figcli.commands.types.config import ConfigCommand
from figcli.commands.config_context import ConfigContext
from figgy.data.dao.config import ConfigDao
from figgy.models.replication_config import ReplicationConfig
from figgy.data.dao.ssm import SsmDao
from figcli.views.rbac_limited_config import RBACLimitedConfigView


class Delete(ConfigCommand):

    def __init__(self, ssm_init: SsmDao, cfg_view: RBACLimitedConfigView,
                 config_init: ConfigDao, repl_init: ReplicationDao, context: ConfigContext, colors_enabled: bool,
                 config_completer: WordCompleter):
        super().__init__(delete, colors_enabled, context)
        self._ssm = ssm_init
        self._config = config_init
        self._repl = repl_init
        self._utils = Utils(colors_enabled)
        self._config_completer = config_completer
        self._out = Output(colors_enabled)
        self._cfg_view = cfg_view

    def delete_param(self, key) -> bool:
        """
        Manages safe deletion through the CLI. Prevents deletion of replication sources. Prompts user for deletion of
        replication destinations.
        Args:
            key: PS Name / Key

        Returns: bool - T/F based on whether a parameter was actually deleted.
        """
        sources = self._repl.get_cfgs_by_src(key)  # type: List[ReplicationConfig]
        repl_conf = self._repl.get_config_repl(key)  # type: ReplicationConfig

        if len(sources) > 0:
            self._out.error(f"You're attempting to delete a key that is the source for at least one "
                            f"replication config.\n[[{key}]] is actively replicating to these"
                            f" destinations:\n")
            for src in sources:
                self._out.warn(f"Dest: [[{src.destination}]]. This config was created by [[{src.user}]]. ")

            self._out.print(
                f"\r\n[[{key}]] is a replication SOURCE. Deleting this source would effectively BREAK "
                f"replication to the above printed destinations. You may NOT delete sources that are actively "
                f"replicating. Please delete the above printed DESTINATIONS first. "
                f"Once they have been deleted, you will be allowed to delete this "
                f"SOURCE.")
            return False
        elif repl_conf is not None:
            selection = "unselected"
            while selection.lower() != "y" and selection.lower() != "n":
                repl_msg = [
                    (f'class:{self.c.rd}', f"{key} is an active replication destination created by "),
                    (f'class:{self.c.bl}', f"{repl_conf.user}. "),
                    (f'class:{self.c.rd}', f"Do you want to ALSO delete this replication config and "
                                           f"permanently delete {key}? "),
                    (f'class:', "(y/N): ")]
                selection = prompt(repl_msg, completer=WordCompleter(['Y', 'N']), style=FIGGY_STYLE)
                selection = selection if selection != '' else 'n'
                if selection.strip().lower() == "y":
                    self._repl.delete_config(key)
                    self._ssm.delete_parameter(key)
                    self._out.success(f"[[{key}]] and replication config destination deleted successfully.")
                    return True
                elif selection.strip().lower() == "n":
                    return False

        else:
            try:
                self._ssm.delete_parameter(key)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ParameterNotFound':
                    pass
                elif "AccessDeniedException" == e.response['Error']['Code']:
                    self._out.error(f"You do not have permissions to delete: {key}")
                    return False
                else:
                    raise

            print(f"{self.c.fg_gr}{key} deleted successfully.{self.c.rs}\r\n")
            return True

    def _delete_param(self):
        """
        Prompts user for a parameter name to delete, then deletes
        """
        # Add all keys
        key, notify, delete_another = None, False, True

        while delete_another:
            key = Input.input('PS Name to Delete: ', completer=self._config_completer)
            try:
                if self.delete_param(key):
                    if key in self._config_completer.words:
                        self._config_completer.words.remove(key)
                else:
                    continue
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if "AccessDeniedException" == error_code:
                    self._out.error(f"\n\nYou do not have permissions to delete config values at the path: [[{key}]]")
                    self._out.warn(f"Your role of {self.context.role} may delete keys under the following namespaces: "
                                   f"{self._cfg_view.get_authorized_namespaces()}")
                    self._out.print(f"Error message: {e.response['Error']['Message']}")
                elif "ParameterNotFound" == error_code:
                    self._out.error(f"The specified Name: [[{key}]] does not exist in the selected environment. "
                                    f"Please try again.")
                else:
                    self._out.error(f"Exception caught attempting to delete config: {e.response['Message']}")

            print()
            to_continue = input(f"Delete another? (Y/n): ")
            to_continue = to_continue if to_continue != '' else 'y'
            delete_another = to_continue.lower() == "y"

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self._delete_param()
