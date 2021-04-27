import logging
from threading import Thread
from typing import List

from flask import Flask, send_from_directory
from flask_cors import CORS

from figcli.commands.command_context import CommandContext
from figcli.svcs.auth.session_manager import SessionManager
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.api.audit import AuditController
from figcli.ui.api.config import ConfigController
from figcli.ui.api.investigate import InvestigateController
from figcli.ui.api.maintenance import MaintenanceController
from figcli.ui.api.usage import UsageController
from figcli.ui.api.user import UserController
from figcli.ui.controller import Controller

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

    def init_controllers(self):
        self.controllers.append(UserController('/user', self._context, self._svc_registry))
        self.controllers.append(ConfigController('/config', self._context, self._svc_registry))
        self.controllers.append(MaintenanceController('/maintenance', self._context, self._svc_registry))
        self.controllers.append(AuditController('/audit', self._context, self._svc_registry))
        self.controllers.append(UsageController('/usage', self._context, self._svc_registry))
        self.controllers.append(InvestigateController('/investigate', self._context, self._svc_registry))

    def run_app(self):
        self.app.add_url_rule('/', 'index', self._goto_index, methods=['GET'])
        self.app.run(host='127.0.0.1', port=5000, debug=False)

    def _goto_index(self):
        return self._serve_page("index.html")

    def _serve_page(self, file_relative_path_to_root):
        return send_from_directory(self._static_files_root_folder_path, file_relative_path_to_root)

    def run(self):
        CORS(self.app)
        for ctlr in self.controllers:
            for route in ctlr.routes():
                self.app.add_url_rule(f'{ctlr.prefix}{route.url_path}', f'{route.url_path}{route.methods[0]}',
                                      view_func=route.fn, methods=route.methods)

        for rule in self.app.url_map.iter_rules():
            log.info(rule)

        app_thread = Thread(target=self.run_app, args=())
        app_thread.start()
