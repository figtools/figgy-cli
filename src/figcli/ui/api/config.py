import logging
from abc import ABC
from typing import Dict, Union, List

from figgy.models.fig import Fig
from figgy.models.n_replication_config import NReplicationConfig
from figgy.models.replication_config import ReplicationConfig
from flask import request, Response

from figcli.commands.config_context import ConfigContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.config_orchard import ConfigOrchard
from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.route import Route

log = logging.getLogger(__name__)

# Todo: Create replicatoin config controller and migrate stuff
class ConfigController(Controller, ABC):

    def __init__(self, prefix: str, config_context: ConfigContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, svc_registry)
        self.registry = svc_registry
        self.context: ConfigContext = config_context
        self._routes.append(Route('', self.get_config, ["GET"]))
        self._routes.append(Route('', self.save_fig, ["POST"]))
        self._routes.append(Route('', self.delete_fig, ["DELETE"]))
        self._routes.append(Route('/names', self.get_config_names, ["GET"]))
        self._routes.append(Route('/tree', self.get_browse_tree, ["GET"]))
        self._routes.append(Route('/isEncrypted', self.is_encrypted, ["GET"]))
        self._routes.append(Route('/isReplDest', self.is_repl_dest, ["GET"]))
        self._routes.append(Route('/isReplSource', self.is_repl_source, ["GET"]))
        self._routes.append(Route('/replicationKey', self.get_replication_key, ["GET"]))
        self._routes.append(Route('/replicationSource', self.get_replication_source, ["GET"]))
        self._routes.append(Route('/replicationDestinations', self.get_replication_destinations, ["GET"]))
        self._routes.append(Route('/replicationConfig', self.get_replication_config, ["GET"]))

    @Controller.client_cache(seconds=5)
    @Controller.build_response()
    def get_config_names(self) -> dict[str, list[str]]:
        req_filter = request.args.get('filter')
        if req_filter:
            return {'names': list(self._cfg().get_parameter_names_by_filter(req_filter))}
        else:
            return {'names': list(self._cfg().get_parameter_names())}

    @Controller.build_response()
    def get_browse_tree(self) -> ConfigOrchard:
        tree = self._cfg_view().get_config_orchard()
        return tree

    # @Controller.client_cache(seconds=5)
    @Controller.build_response()
    def get_config(self) -> Union[Fig, FiggyResponse]:
        name = request.args.get('name')
        type = request.args.get('type')
        version = int(request.args.get('version', 0))

        if type == 'full':
            fig = self._cfg().get_fig(name, version=version)
        elif type == 'simple':
            fig = self._cfg().get_fig_simple(name)
        else:
            fig = self._cfg().get_fig(name, version=version)

        if fig.is_missing():
            return FiggyResponse.fig_missing()
        else:
            return fig


    # @Controller.client_cache(seconds=10)
    @Controller.build_response()
    def is_encrypted(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_encrypted': self._cfg().is_encrypted(name)}

    # @Controller.client_cache(seconds=10)
    @Controller.build_response()
    def is_repl_source(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_repl_source': self._cfg().is_replication_source(name)}

    # @Controller.client_cache(seconds=10)
    @Controller.build_response()
    def is_repl_dest(self):
        # Todo add validation for expected args with decorator
        name = request.args.get('name')
        return {'is_repl_dest': self._cfg().is_replication_destination(name)}

    @Controller.build_response()
    def save_fig(self):
        payload: Dict = request.json
        fig: Fig = Fig(**payload)
        log.info(f"SAVING FIG: {fig}")
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

    @Controller.build_response()
    def delete_fig(self):
        name = request.args.get('name')
        self._cfg().delete(name)

    @Controller.build_response()
    def get_replication_destinations(self) -> List[NReplicationConfig]:
        source = request.args.get('name')

        return self._cfg().get_replication_configs_by_source(source)

    @Controller.build_response()
    def get_replication_config(self):
        source = request.args.get('name')

        return self._cfg().get_replication_config(source)
