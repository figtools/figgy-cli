import time

from figgy.data.dao.audit import AuditDao
from figgy.data.dao.replication import ReplicationDao

from figcli.config import *
from datetime import datetime
from typing import List

from botocore.exceptions import ClientError
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from tabulate import tabulate

from figcli.commands.config.delete import Delete
from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figgy.data.dao.config import ConfigDao
from figgy.data.dao.ssm import SsmDao
from figcli.io.input import Input
from figcli.io.output import Output
from figgy.models.parameter_store_history import PSHistory
from figgy.models.replication_config import ReplicationConfig
from figgy.models.restore_config import RestoreConfig
from figcli.svcs.kms import KmsService
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import Utils
from figcli.views.rbac_limited_config import RBACLimitedConfigView


class Restore(ConfigCommand):
    def __init__(
            self,
            ssm_init: SsmDao,
            kms_init: KmsService,
            config_init: ConfigDao,
            repl_dao: ReplicationDao,
            audit_dao: AuditDao,
            cfg_view: RBACLimitedConfigView,
            colors_enabled: bool,
            context: ConfigContext,
            config_completer: WordCompleter,
            delete: Delete
    ):
        super().__init__(restore, colors_enabled, context)
        self._config_context = context
        self._ssm = ssm_init
        self._kms = kms_init
        self._config = config_init
        self._repl = repl_dao
        self._audit = audit_dao
        self._cfg_view = cfg_view
        self._utils = Utils(colors_enabled)
        self._point_in_time = context.point_in_time
        self._config_completer = config_completer
        self._delete = delete
        self._out = Output(colors_enabled=colors_enabled)

    def _client_exception_msg(self, item: RestoreConfig, e: ClientError):
        if "AccessDeniedException" == e.response["Error"]["Code"]:
            self._out.error(f"\n\nYou do not have permissions to restore config at the path: [[{item.ps_name}]]")
        else:
            self._out.error(f"Error message: [[{e.response['Error']['Message']}]]")

    def get_parameter_arn(self, parameter_name: str):
        account_id = self._ssm.get_parameter(ACCOUNT_ID_PATH)

        return f"arn:aws:ssm:us-east-1:{account_id}:parameter{parameter_name}"

    def _restore_param(self) -> None:
        """
        Allow the user to query a parameter store entry from dynamo, so we can query + restore it, if desired.
        """

        table_entries = []

        ps_name = prompt(f"Please input PS key to restore: ", completer=self._config_completer)

        if self._is_replication_destination(ps_name):
            repl_conf = self._repl.get_config_repl(ps_name)
            self._print_cannot_restore_msg(repl_conf)
            exit(0)

        self._out.notify(f"\n\nAttempting to retrieve all restorable values of [[{ps_name}]]")
        items: List[RestoreConfig] = self._audit.get_parameter_restore_details(ps_name)

        if len(items) == 0:
            self._out.warn("No restorable values were found for this parameter.")
            return

        for i, item in enumerate(items):
            date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.ps_time / 1000))

            # we need to decrypt the value, if encrypted, in order to show it to the user
            if item.ps_key_id:
                item.ps_value = self._kms.decrypt_with_context(
                    item.ps_value,
                    {"PARAMETER_ARN": self.get_parameter_arn(item.ps_name)},
                )
            table_entries.append([i, date, item.ps_value, item.ps_user])

        self._out.print(
            tabulate(
                table_entries,
                headers=["Item #", "Time Created", "Value", "User"],
                tablefmt="grid",
                numalign="center",
                stralign="left",
            )
        )

        valid_options = [f'{x}' for x in range(0, len(items))]
        choice = int(Input.select("Select an item number to restore: ", valid_options=valid_options))
        item = items[choice] if items[choice] else None

        restore = Input.y_n_input(
            f"Are you sure you want to restore item #{choice} and have it be the latest version? ",
            default_yes=False)

        if not restore:
            self._utils.warn_exit("Restore aborted.")

        key_id = None if item.ps_type == "String" else item.ps_key_id

        try:
            self._ssm.set_parameter(item.ps_name, item.ps_value, item.ps_description, item.ps_type, key_id=key_id)

            current_value = self._ssm.get_parameter(item.ps_name)
            if current_value == item.ps_value:
                self._out.success("Restore was successful")
            else:
                self._out.error("Latest version in parameter store doesn't match what we restored.")
                self._out.print(f"Current value: [[{current_value}]].  Expected value: [[{item.ps_value}]]")

        except ClientError as e:
            self._client_exception_msg(item, e)

    def _decrypt_if_applicable(self, entry: RestoreConfig) -> str:
        if entry.ps_type != "String":
            return self._kms.decrypt_with_context(
                entry.ps_value, {"PARAMETER_ARN": self.get_parameter_arn(entry.ps_name)}
            )
        else:
            return entry.ps_value

    def _is_replication_destination(self, ps_name: str):
        return self._repl.get_config_repl(ps_name)

    def _restore_params_to_point_in_time(self):
        """
        Restores parameters as they were to a point-in-time as defined by the time provided by the users.
        Replays parameter history to that point-in-time so versioning remains intact.
        """

        repl_destinations = []
        ps_prefix = Input.input(f"Which parameter store prefix would you like to recursively restore? "
                           f"(e.g., /app/demo-time): ", completer=self._config_completer)

        authed_nses = self._cfg_view.get_authorized_namespaces()
        valid_prefix = ([True for ns in authed_nses if ps_prefix.startswith(ns)] or [False])[0]
        self._utils.validate(valid_prefix, f"Selected namespace must begin with a 'Fig Tree' you have access to. "
                                           f"Such as: {authed_nses}")

        time_selected, time_converted = None, None
        try:
            time_selected = Input.input("Seconds since epoch to restore latest values from: ")
            time_converted = datetime.fromtimestamp(float(time_selected))
        except ValueError as e:
            if "out of range" in e.args[0]:
                try:
                    time_converted = datetime.fromtimestamp(float(time_selected) / 1000)
                except ValueError as e:
                    self._utils.error_exit(
                        "Make sure you're using a format of either seconds or milliseconds since epoch.")
            elif "could not convert" in e.args[0]:
                self._utils.error_exit(f"The format of this input should be seconds since epoch. (e.g., 1547647091)\n"
                                       f"Try using: https://www.epochconverter.com/ to convert your date to this "
                                       f"specific format.")
            else:
                self._utils.error_exit("An unexpected exception triggered: "
                                       f"'{e}' while trying to convert {time_selected} to 'datetime' format.")

        self._utils.validate(time_converted is not None, f"`{CLI_NAME}` encountered an error parsing your input for "
                                                         f"target rollback time.")
        keep_going = Input.y_n_input(
            f"Are you sure you want to restore all figs under {ps_prefix} values to their state at: "
            f"{time_converted}? ", default_yes=False
        )

        if not keep_going:
            self._utils.warn_exit("Aborting restore due to user selection")

        ps_history: PSHistory = self._audit.get_parameter_history_before_time(time_converted, ps_prefix)
        restore_count = len(ps_history.history.values())

        if len(ps_history.history.values()) == 0:
            self._utils.warn_exit("No results found for time range.  Aborting.")

        last_item_name = 'Unknown'
        try:
            for item in ps_history.history.values():
                last_item_name = item.name

                if self._is_replication_destination(item.name):
                    repl_destinations.append(item.name)
                    continue

                if item.cfg_at(time_converted).ps_action == SSM_PUT:
                    cfgs_before: List[RestoreConfig] = item.cfgs_before(time_converted)
                    cfg_at: RestoreConfig = item.cfg_at(time_converted)
                    ssm_value = self._ssm.get_parameter(item.name)
                    dynamo_value = self._decrypt_if_applicable(cfg_at)

                    if ssm_value != dynamo_value:
                        if ssm_value is not None:
                            self._ssm.delete_parameter(item.name)

                        for cfg in cfgs_before:
                            decrypted_value = self._decrypt_if_applicable(cfg)
                            self._out.print(f"\nRestoring: [[{cfg.ps_name}]] \nValue: [[{decrypted_value}]]"
                                             f"\nDescription: [[{cfg.ps_description}]]\nKMS Key: "
                                             f"[[{cfg.ps_key_id if cfg.ps_key_id else '[[No KMS Key Specified]]'}]]")
                            self._out.notify(f"Replaying version: [[{cfg.ps_version}]] of [[{cfg.ps_name}]]")
                            print()

                            self._ssm.set_parameter(cfg.ps_name, decrypted_value,
                                                    cfg.ps_description, cfg.ps_type, key_id=cfg.ps_key_id)
                    else:
                        self._out.success(f"Config: {item.name} is current. Skipping.")
                else:
                    # This item must have been a delete, which means this config didn't exist at that time.
                    self._out.print(f"Checking if [[{item.name}]] exists. It was previously deleted.")
                    self._prompt_delete(item.name)
        except ClientError as e:
            if "AccessDeniedException" == e.response["Error"]["Code"]:
                self._utils.error_exit(f"\n\nYou do not have permissions to restore config at the path:"
                                       f" [[{last_item_name}]]")
            else:
                self._utils.error_exit(f"Caught error when attempting restore. {e}")

        for item in repl_destinations:
            cfg = self._repl.get_config_repl(item)
            self._print_cannot_restore_msg(cfg)

        print("\n\n")
        if not repl_destinations:
            self._out.success_h2(f"[[{restore_count}]] configurations restored successfully!")
        else:
            self._out.warn(f"\n\n[[{len(repl_destinations)}]] configurations were not restored because they are shared "
                           f"from other destinations. To restore them, restore their sources.")
            self._out.success(f"{restore_count - len(repl_destinations)} configurations restored successfully.")

    def _print_cannot_restore_msg(self, repl_conf: ReplicationConfig):
        self._out.print(f"Parameter: [[{repl_conf.destination}]] is a shared parameter. ")
        self._out.print(f"Shared From: [[{repl_conf.source}]]")
        self._out.print(f"Shared by: [[{repl_conf.user}]]")
        self._out.warn(f"To restore this parameter you should restore the source: {repl_conf.source} instead!")
        print()

    def _prompt_delete(self, name):
        param = self._ssm.get_parameter_encrypted(name)
        if param:
            selection = Input.y_n_input(f"PS Name: {name} did not exist at this restore time."
                                        f" Delete it? ", default_yes=False)

            if selection:
                self._delete.delete_param(name)

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        if self._point_in_time:
            self._restore_params_to_point_in_time()
        else:
            self._restore_param()
