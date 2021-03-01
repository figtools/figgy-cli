from threading import Thread
from typing import Optional, List
from figgy.data.dao.ssm import SsmDao
from flask import Flask, render_template
from flask_cors import CORS

from figcli.commands.config_context import ConfigContext
from figcli.svcs.config import ConfigService
from figcli.ui.api.config import ConfigController
from figcli.ui.api.user import UserController
from figcli.ui.controller import Controller
from figcli.views.rbac_limited_config import RBACLimitedConfigView


class App:
    def __init__(self, ssm: SsmDao, context: ConfigContext, config_svc: ConfigService, config_view: RBACLimitedConfigView):
        self._ssm = ssm
        self._context = context
        self._config_svc = config_svc
        self._config_view = config_view
        self.app: Flask = Flask(__name__, static_folder='assets', static_url_path='')
        self.controllers: List[Controller] = []
        self.init_controllers()

    def init_controllers(self):
        self.controllers.append(UserController('/user', self._context))
        self.controllers.append(ConfigController('/config', self._context, self._config_svc, self._config_view))

    def run_app(self):
        self.app.run(host='0.0.0.0', port=5000, debug=False)

    def run(self):
        CORS(self.app)
        for ctlr in self.controllers:
            for route in ctlr.routes():
                self.app.add_url_rule(f'{ctlr.prefix}{route.url_path}', route.url_path, route.fn)

        for rule in self.app.url_map.iter_rules():
            print(rule)

        app_thread = Thread(target=self.run_app, args=())
        app_thread.start()
