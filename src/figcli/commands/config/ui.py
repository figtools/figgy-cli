import webbrowser
from figcli.commands.command_context import CommandContext
from figcli.commands.types.command import Command
from figcli.svcs.auth.session_manager import SessionManager
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import *

log = logging.getLogger(__name__)


class UI(Command):

    def __init__(self, context: CommandContext, session_mgr: SessionManager):
        super().__init__(ui, context.defaults.colors_enabled, context)
        self._session_mgr = session_mgr
        self._utils = Utils(context.defaults.colors_enabled)
        self._out = Output(context.defaults.colors_enabled)


    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        from figcli.ui.app import App
        try:
            app = App(self.context, self._session_mgr)
            app.run()
            self._out.success_h2("Loading Figgy UI")
            webbrowser.open("http://localhost:5000/")
            # Wait for Ctrl C to exit...
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._out.success_h2("Exiting Figgy UI. Have a great day!")
            pass
