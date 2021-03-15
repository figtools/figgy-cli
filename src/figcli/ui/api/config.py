import logging
from abc import ABC
from typing import Dict

from figgy.models.fig import Fig
from flask import request

from figcli.commands.config_context import ConfigContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.config_orchard import ConfigOrchard
from figcli.ui.route import Route

log = logging.getLogger(__name__)


class ConfigController(Controller, ABC):

    def __init__(self, prefix: str, config_context: ConfigContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, svc_registry)
        self.registry = svc_registry
        self.context: ConfigContext = config_context
        self._routes.append(Route('', self.get_config, ["GET"]))
        self._routes.append(Route('', self.save_fig, ["POST"]))
        self._routes.append(Route('/names', self.get_config_names, ["GET"]))
        self._routes.append(Route('/tree', self.get_browse_tree, ["GET"]))
        self._routes.append(Route('/isEncrypted', self.is_encrypted, ["GET"]))
        self._routes.append(Route('/isReplDest', self.is_repl_dest, ["GET"]))
        self._routes.append(Route('/isReplSource', self.is_repl_source, ["GET"]))
        self._routes.append(Route('/replicationKey', self.get_replication_key, ["GET"]))
        self._routes.append(Route('/replicationSource', self.get_replication_source, ["GET"]))

    @Controller.client_cache(seconds=10)
    @Controller.build_response()
    def get_config_names(self) -> dict[str, list[str]]:
        req_filter = request.args.get('filter')
        if req_filter:
            return {'names': list(self._cfg().get_parameter_names_by_filter(req_filter))}
        else:
            return {'names': list(self._cfg().get_parameter_names())}

    @Controller.client_cache(seconds=30)
    @Controller.build_response()
    def get_browse_tree(self) -> ConfigOrchard:
        return self._cfg_view().get_config_orchard()

    @Controller.client_cache(seconds=5)
    @Controller.build_response()
    def get_config(self) -> Fig:
        name = request.args.get('name')
        type = request.args.get('type')
        if type == 'full':
            return self._cfg().get_fig(name)
        elif type == 'simple':
            return self._cfg().get_fig_simple(name)
        else:
            return self._cfg().get_fig(name)

    @Controller.client_cache(seconds=30)
    @Controller.build_response()
    def is_encrypted(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_encrypted': self._cfg().is_encrypted(name)}

    @Controller.client_cache(seconds=30)
    @Controller.build_response()
    def is_repl_source(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_repl_source': self._cfg().is_replication_source(name)}

    @Controller.client_cache(seconds=30)
    @Controller.build_response()
    def is_repl_dest(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_repl_dest': self._cfg().is_replication_destination(name)}

    @Controller.build_response()
    def save_fig(self):
        payload: Dict = request.json
        fig: Fig = Fig(**payload)
        self._cfg().save(fig)

    @Controller.client_cache(seconds=30)
    @Controller.build_response()
    def get_replication_key(self):
        return {'kms_key_id': self._cfg().get_replication_key()}

    @Controller.client_cache(seconds=30)
    @Controller.build_response()
    def get_replication_source(self):
        name = request.args.get('name')
        return {'source': self._cfg().get_replication_config(name).source}
