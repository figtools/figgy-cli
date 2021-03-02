from abc import ABC
from typing import Set, List, Any

from figgy.models.fig import Fig

from figcli.commands.config_context import ConfigContext
from figcli.svcs.config import ConfigService
from figcli.ui.controller import Controller
from figcli.ui.route import Route
from flask import request

from figcli.views.rbac_limited_config import RBACLimitedConfigView


class ConfigController(Controller, ABC):

    def __init__(self, prefix: str, config_context: ConfigContext, config_svc: ConfigService,
                 config_view: RBACLimitedConfigView):
        super().__init__(prefix)
        self.context: ConfigContext = config_context
        self._routes.append(Route('', self.get_config, ["GET"]))
        self._routes.append(Route('/names', self.get_config_names, ["GET"]))
        self._routes.append(Route('/tree', self.get_browse_tree, ["GET"]))
        self._config_svc = config_svc
        self._cfg_view = config_view

    def get_config_names(self) -> dict[str, list[str]]:
        print(f"Got request: {request}")
        print(f"Got request: {request}")
        req_filter = request.args.get('filter')
        if req_filter:
            return {'names': list(self._config_svc.get_parameter_names_by_filter(req_filter))}
        else:
            return {'names': list(self._config_svc.get_parameter_names())}

    def get_browse_tree(self) -> dict[str, Any]:
        return self._cfg_view.get_config_orchard().__dict__

    def get_config(self) -> Fig:
        name = request.args.get('name')
        return self._config_svc.get_fig_simple(name)
