from abc import ABC

from figcli.commands.ots_context import OTSContext
from figcli.commands.types.command import Command
from figcli.models.cli_command import CliCommand


class OTSCommand(Command, ABC):
    """
    OTS command class from which all other ots command classes inherit.
    """

    def __init__(self, command_type: CliCommand, colors_enabled: bool, context: OTSContext):
        super().__init__(command_type, colors_enabled, context)
        self.role = context.role
