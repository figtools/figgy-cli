import json
import logging
from abc import ABC
from typing import Set, List, Any, Dict

from botocore.exceptions import ClientError
from figgy.models.fig import Fig

from figcli.commands.config_context import ConfigContext
from figcli.models.assumable_role import AssumableRole
from figcli.svcs.config import ConfigService
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.config_orchard import ConfigOrchard
from figcli.ui.route import Route
from flask import request

from figcli.utils.utils import Utils
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


class ConfigController(Controller, ABC):

    def __init__(self, prefix: str, config_context: ConfigContext, svc_registry: ServiceRegistry):
        super().__init__(prefix)
        self.registry = svc_registry
        self.context: ConfigContext = config_context
        self._routes.append(Route('', self.get_config, ["GET"]))
        self._routes.append(Route('/names', self.get_config_names, ["GET"]))
        self._routes.append(Route('/tree', self.get_browse_tree, ["GET"]))
        self._routes.append(Route('/isEncrypted', self.is_encrypted, ["GET"]))
        self._routes.append(Route('/isReplDest', self.is_repl_dest, ["GET"]))
        self._routes.append(Route('/isReplSource', self.is_repl_source, ["GET"]))

    def __cfg(self):
        active_role = json.loads(request.headers.get('ActiveRole'))
        return self.registry.config_svc(AssumableRole(**active_role))

    def __cfg_view(self):
        active_role = json.loads(request.headers.get('ActiveRole'))
        return self.registry.rbac_view(AssumableRole(**active_role))

    def get_config_names(self) -> dict[str, list[str]]:
        print(f"Got request: {request}")
        req_filter = request.args.get('filter')
        if req_filter:
            return {'names': list(self.__cfg().get_parameter_names_by_filter(req_filter))}
        else:
            return {'names': list(self.__cfg().get_parameter_names())}

    @Controller.return_json
    def get_browse_tree(self) -> ConfigOrchard:
        return self.__cfg_view().get_config_orchard()


    @Controller.return_json
    def get_config(self) -> Fig:
        name = request.args.get('name')
        type = request.args.get('type')

        if type == 'full':
            return self.__cfg().get_fig(name)
        elif type == 'simple':
            return self.__cfg().get_fig_simple(name)
        else:
            return self.__cfg().get_fig(name)

    def is_encrypted(self) -> Dict:
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_encrypted': self.__cfg().is_encrypted(name)}

    def is_repl_source(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_repl_source': self.__cfg().is_replication_source(name)}

    def is_repl_dest(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_repl_dest': self.__cfg().is_replication_destination(name)}
