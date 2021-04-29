from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figcli.svcs.auth.session_manager import SessionManager
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.utils.utils import *


class BuildCache(ConfigCommand):
    """
    Logs into every feasible AWS account/region/session and hydrates a local cache. Doesn't need to be run, but if it is
    run, run it once :)
    """

    def __init__(self, session_manager: SessionManager, colors_enabled: bool, config_context: ConfigContext):
        super().__init__(build_cache, colors_enabled, config_context)
        self._session_mgr = session_manager
        self._utils = Utils(colors_enabled)
        self._out = Output(colors_enabled)
        self._svc_registry = ServiceRegistry(self._session_mgr, self.context)

    def _build_cache(self):
        roles = self.context.defaults.assumable_roles
        regions = self.context.defaults.enabled_regions
        self._out.notify(f'Found {len(roles) * len(regions)} caches to build.')

        for role in roles:
            for region in regions:
                self._out.print(f"Building cache for Role: {role.role.role} and region: {region}")
                env = GlobalEnvironment(role=role, region=region)
                self._svc_registry.config_svc(env).get_parameter_names()

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self._build_cache()
