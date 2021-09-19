from abc import ABC

from figcli.commands.maintenance_context import MaintenanceContext
from figcli.commands.types.command import Command


class MaintenanceCommand(Command, ABC):
    """
    Help command class to support some commands that may not have a resource or specific command selected
    """

    def __init__(self, command_type: frozenset, colors_enabled: bool, context: MaintenanceContext):
        super().__init__(command_type, colors_enabled, context)
