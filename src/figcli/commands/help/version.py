from figcli.commands.maintenance_context import MaintenanceContext
from figcli.commands.types.maintenance import MaintenanceCommand
from figcli.config import *
from figcli.svcs.config import ConfigService
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker


class Version(MaintenanceCommand):
    """
    Drives the --version command
    """

    def __init__(self, maint_context: MaintenanceContext, config_service: ConfigService):
        super().__init__(version, maint_context.defaults.colors_enabled, maint_context)
        self.tracker = VersionTracker(self.context.defaults, config_service)

    def version(self):
        self.tracker.check_version(self.c)

    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self.version()
