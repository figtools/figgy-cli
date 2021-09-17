import logging
import os
from threading import Thread
from typing import List

from flask import Flask, send_from_directory
from flask_cors import CORS

from figcli.commands.command_context import CommandContext
from figcli.models.user.user import User
from figcli.svcs.auth.session_manager import SessionManager
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.api.audit import AuditController
from figcli.ui.api.config import ConfigController
from figcli.ui.api.investigate import InvestigateController
from figcli.ui.api.maintenance import MaintenanceController
from figcli.ui.api.one_time_secret import OTSController
from figcli.ui.api.usage import UsageController
from figcli.ui.api.user import UserController
from figcli.ui.controller import Controller
from figcli.ui.models.global_environment import GlobalEnvironment

log = logging.getLogger(__name__)


class App:
    def __init__(self, context: CommandContext, session_mgr: SessionManager):
        self._context = context
        self._session_mgr = session_mgr
        self._svc_registry = ServiceRegistry(self._session_mgr, self._context)
        self._static_files_root_folder_path = 'assets'
        self.app: Flask = Flask(__name__, static_folder='assets', static_url_path='', template_folder='templates')
        self.controllers: List[Controller] = []
        self.init_controllers()
        # self.build_sessions()

    def build_sessions(self):
        envs: List[GlobalEnvironment] = []
        self.user = User(name=self._context.defaults.user,
                         role=self._context.defaults.role,
                         assumable_roles=self._context.defaults.assumable_roles,
                         enabled_regions=self._context.defaults.enabled_regions
                                         or [self._context.defaults.region])

        for role in self.user.assumable_roles:
            for region in self.user.enabled_regions:
                envs.append(GlobalEnvironment(role=role, region=region))

        self._svc_registry.auth_roles(envs)

    def init_controllers(self):
        self.controllers.append(UserController('/user', self._context, self._svc_registry))
        self.controllers.append(ConfigController('/config', self._context, self._svc_registry))
        self.controllers.append(MaintenanceController('/maintenance', self._context, self._svc_registry))
        self.controllers.append(AuditController('/audit', self._context, self._svc_registry))
        self.controllers.append(UsageController('/usage', self._context, self._svc_registry))
        self.controllers.append(InvestigateController('/investigate', self._context, self._svc_registry))
        self.controllers.append(OTSController('/', self._context, self._svc_registry))

    def run_app(self):
        self.app.add_url_rule('/', 'index', self._goto_index, methods=['GET'])
        # Todo set back to 127.0.0.1 after docker demos.
        self.app.run(host='0.0.0.0', port=5000, debug=False)

    def _goto_index(self):
        return self._serve_page("index.html")

    def _serve_page(self, file_relative_path_to_root):
        return send_from_directory(self._static_files_root_folder_path, file_relative_path_to_root, cache_timeout=-1)

    def run(self):
        # Disables prod Flask warning. Base flask is not an issue due to our single-user case.
        os.environ["WERKZEUG_RUN_MAIN"] = "true"

        CORS(self.app)
        for ctlr in self.controllers:
            for route in ctlr.routes():
                self.app.add_url_rule(f'{ctlr.prefix}{route.url_path}', f'{route.url_path}{route.methods[0]}',
                                      view_func=route.fn, methods=route.methods)

        for rule in self.app.url_map.iter_rules():
            log.info(rule)

        app_thread = Thread(target=self.run_app, args=())
        app_thread.daemon = True
        app_thread.start()
