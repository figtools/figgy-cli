from collections import namedtuple
from typing import Optional

from boto3.session import Session

from figcli.commands.iam_context import IAMContext
from figcli.commands.types.iam import IAMCommand
from figcli.svcs.aws_cfg import AWSConfig
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.utils.utils import *


class Restore(IAMCommand):
    """
    Returns audit history for a queried PS Name
    """

    def __init__(self, iam_context: IAMContext):
        super().__init__(restore, iam_context)
        self._aws_cfg = AWSConfig(color=self.c)

    def _restore(self):
        self._aws_cfg.restore('default')

    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self._restore()
