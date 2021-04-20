from typing import Optional

import boto3
from figgy.data.dao.config import ConfigDao
from figgy.data.dao.ssm import SsmDao

from figcli.models.cli_command import CliCommand
from figcli.models.defaults.defaults import CLIDefaults
from figgy.models.run_env import RunEnv

from figcli.svcs.kms import KmsService


class CommandContext:
    """
    All commands, regardless of resource type, will need to know what RunEnvironment they are operating on. That is the
    purpose of this command context. Similar properties would be added here.
    """
    def __init__(self, run_env: RunEnv, resource: CliCommand, defaults: Optional[CLIDefaults]):
        self.run_env = run_env  # type: RunEnv
        self.resource = resource
        self.defaults = defaults
