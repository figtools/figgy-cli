from typing import Optional

from figgy.models.run_env import RunEnv

from figcli.commands.command_context import CommandContext
from figcli.config import ots
from figcli.models.defaults.defaults import CLIDefaults
from figcli.models.role import Role


class OTSContext(CommandContext):
    """
    All `ots` resource commands require this context for general use.

    The context contains optional parameter values passed in via the original invoked command vai the CLI
    """

    def __init__(self, run_env: RunEnv, role: Role, defaults: Optional[CLIDefaults]):
        super().__init__(run_env, ots, defaults=defaults)
        self.run_env = run_env
        self.role = role
        self.resource = ots
        self.defaults = defaults
