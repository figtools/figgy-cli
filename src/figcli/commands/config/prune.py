from typing import Dict, Set

from figgy.data.dao.replication import ReplicationDao

from figcli.config.commands import *
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from figcli.config.constants import *
from figcli.commands.config.delete import Delete
from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figcli.config.style.style import FIGGY_STYLE
from figcli.io.input import Input
from figgy.data.dao.config import ConfigDao
from figgy.data.dao.ssm import SsmDao
from figcli.extras.key_utils import KeyUtils
from figcli.io.output import Output
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import Utils


class Prune(ConfigCommand):
    """
    Detects stray ParameterStore names, replication configurations, and merge keys, then
    prompts the user to delete them. This is typically run after the `sync` command informs
    the user that there are stray configurations.
    """

    def __init__(self, ssm: SsmDao, ddb: ConfigDao, repl_dao: ReplicationDao, context: ConfigContext,
                 config_completer_init: WordCompleter, colors_enabled: bool, delete: Delete, args=None):
        super().__init__(prune, colors_enabled, context)
        self._ssm = ssm  # type: SsmDao
        self._config_dao = ddb  # type: ConfigDao
        self._repl = repl_dao
        self._config_completer = config_completer_init  # type: WordCompleter
        self._utils = Utils(colors_enabled)
        self.example = f"{self.c.fg_bl}{CLI_NAME} config {self.command_printable} --env dev " \
            f"--config /path/to/figgy.json{self.c.rs}"
        self._config_path = context.ci_config_path if context.ci_config_path else Utils.find_figgy_json()
        self._out = Output(colors_enabled)

        # If user passes in --info flag, we don't need all of this to be initialized.
        if not hasattr(args, info.name) or args.info is False:
            # Validate & parse figgy.json
            self._config = self._utils.get_ci_config(self._config_path)  # type: Dict
            self._shared_names = set(self._utils.get_config_key_safe(SHARED_KEY, self._config, default=[]))  # type: Set
            self._repl_conf = self._utils.get_config_key_safe(REPLICATION_KEY, self._config, default={})  # type: Dict
            self._merge_conf = self._utils.get_config_key_safe(MERGE_KEY, self._config, default={})  # type: Dict
            self._config_keys = set(self._utils.get_config_key_safe(CONFIG_KEY, self._config, default=[]))  # type: Set
            self._merge_keys = set(self._merge_conf.keys())  # type: Set
            self._namespace = self._utils.get_namespace(self._config)  # type: str
            self._delete_command = delete
            self._repl_from_conf = self._utils.get_config_key_safe(REPL_FROM_KEY, self._config, default={})
            self._repl_conf = KeyUtils.merge_repl_and_repl_from_blocks(self._repl_conf, self._repl_from_conf,
                                                                       self._namespace)

            # Build list of all keys found across all config types
            self._all_keys = KeyUtils().find_all_expected_names(self._config_keys, self._shared_names, self._merge_conf,
                                                                self._repl_conf, self._repl_from_conf, self._namespace)

    # Prompts for this file
    def _cleanup_parameters(self, config_keys: Set):
        """
        Prompts user for prune of stray ParameterStore names.
        Args:
            config_keys: set() -> Set of parameters that are found as defined in the figgy.json file for a svc
        """

        self._out.notify(f"Checking for stray config names.\r\n")

        # Find & Prune stray keys
        ps_keys = set(list(map(lambda x: x['Name'], self._ssm.get_all_parameters([self._namespace]))))
        ps_only_keys = ps_keys.difference(config_keys)
        for key in ps_only_keys:
            selection = Input.y_n_input(f"{key} exists in ParameterStore but does not exist "
                                        f"in your config, do you want to delete it?", default_yes=False)

            if selection:
                self._delete_command.delete_param(key)
            else:
                self._out.notify("OK, skipping due to user selection.")
        if not ps_only_keys:
            print(f"{self.c.fg_bl}No stray keys found.{self.c.rs}")

    def _cleanup_replication(self) -> None:
        """
        Cleans up stray replication and merge configurations.
        Args:
            config_repl: The replication config dictionary as parsed from the figgy.json file
            shared_names: Expected parameters as defined in the figgy.json
            config_merge: The merge config dict as defined
            run_env: RunEnv object
            namespace: str -> /app/service-name as defined or parsed from the figgy.json file.
        """

        self._out.notify(f"Checking for stray replication configs.")
        remote_cfgs = self._repl.get_all_configs(self._namespace)
        notify = True
        if remote_cfgs:
            for cfg in remote_cfgs:
                if cfg.source not in list(self._repl_conf.keys()) \
                        and cfg.destination not in list(self._repl_conf.values()) \
                        and cfg.destination not in self._shared_names \
                        and cfg.destination not in list(self._merge_conf.keys()) \
                        and (isinstance(cfg.source, list) or cfg.source.startswith(shared_ns)
                             or cfg.source.startswith(self.context.defaults.service_ns)):
                    notify = False

                    selection = "unselected"
                    while selection.lower() != "y" and selection.lower() != "n":
                        selection = input(
                            f"Remote replication config with {self.c.fg_bl}{self._namespace}{self.c.rs} replication "
                            f"mapping of: {self.c.fg_bl}{cfg.source} -> {cfg.destination}{self.c.rs} does not "
                            f"exist in your figgy.json. Should this be removed? (y/N): ").lower()
                        selection = selection if selection != '' else 'n'
                        if selection == "y":
                            self._repl.delete_config(cfg.destination)
        if notify:
            self._out.success("No remote replication configs found available for prune under namespace: "
                              f"[[{self._namespace}]]")

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        # prune service configs
        print()
        self._cleanup_parameters(set(self._all_keys))

        print()
        # prune replication configs
        self._cleanup_replication()
