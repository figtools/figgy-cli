from figgy.data.dao.ssm import SsmDao

from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figcli.svcs.auth.session_manager import SessionManager
from figcli.svcs.config import ConfigService
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import *
from figcli.views.rbac_limited_config import RBACLimitedConfigView
import webbrowser

log = logging.getLogger(__name__)


class UI(ConfigCommand):

    def __init__(self, ssm_init: SsmDao, colors_enabled: bool,
                 config_context: ConfigContext, config_svc: ConfigService,
                 config_view: RBACLimitedConfigView, session_mgr: SessionManager):
        super().__init__(ui, colors_enabled, config_context)
        self._ssm = ssm_init
        self._config_svc = config_svc
        self._config_view = config_view
        self._session_mgr = session_mgr
        self._utils = Utils(colors_enabled)
        self._out = Output(colors_enabled)


    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        from figcli.ui.app import App

        app = App(self.context, self._session_mgr)
        app.run()
        self._out.success_h2("Loading Figgy UI")
        # webbrowser.open("http://localhost:5000/")
