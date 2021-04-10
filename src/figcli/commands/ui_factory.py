from figcli.commands.command_context import CommandContext
from figcli.commands.config.ui import UI
from figcli.commands.factory import Factory
from figcli.commands.figgy_context import FiggyContext
from figcli.config import *
from figcli.svcs.auth.session_manager import SessionManager
from figcli.svcs.setup import FiggySetup
from figcli.utils.utils import Utils, CollectionUtils


class UIFactory(Factory):
    def __init__(self, command: CliCommand,
                 context: CommandContext,
                 session_manager: SessionManager,
                 figgy_context: FiggyContext):
        self._command = command
        self._context = context
        self._utils = Utils(False)
        self._setup: FiggySetup = FiggySetup(figgy_context)
        self._session_manager = session_manager

    def instance(self):
        return self.get(self._command)

    def get(self, command: CliCommand):
        if command == ui:
            return UI(self._context, self._session_manager)
        else:
            self._utils.error_exit(f"{command.name} is not a valid command. You must select from: "
                                   f"[{CollectionUtils.printable_set(ui_commands)}]. Try using --help for more info.")