from figcli.commands.factory import Factory
from figcli.commands.figgy_context import FiggyContext
from figcli.commands.help.upgrade import Upgrade
from figcli.commands.help.version import Version
from figcli.commands.maintenance_context import MaintenanceContext
from figcli.config import *
from figcli.svcs.config import ConfigService
from figcli.svcs.setup import FiggySetup
from figcli.utils.utils import Utils, CollectionUtils


class MaintenanceFactory(Factory):
    def __init__(self, command: CliCommand, context: MaintenanceContext, figgy_context: FiggyContext, config: ConfigService):
        self._command = command
        self._context = context
        self._figgy_context = figgy_context
        self._options = context.options
        self._utils = Utils(False)
        self._setup: FiggySetup = FiggySetup(self._figgy_context)
        self._config: ConfigService = config

    def instance(self):
        return self.get(self._command)

    def get(self, command: CliCommand):
        if version in self._options:
            return Version(self._context, self._config)
        elif upgrade in self._options:
            return Upgrade(self._context, self._config)
        else:
            self._utils.error_exit(f"{command.name} is not a valid command. You must select from: "
                                   f"[{CollectionUtils.printable_set(help_commands)}]. Try using --help for more info.")
