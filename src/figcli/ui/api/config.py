import logging
from abc import ABC
from typing import Dict, Union, List

from figgy.models.fig import Fig
from figgy.models.replication_config import ReplicationConfig
from flask import request

from figcli.commands.command_context import CommandContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.config_orchard import ConfigOrchard
from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.route import Route

log = logging.getLogger(__name__)


# Todo: Create replication config controller and migrate stuff
class ConfigController(Controller, ABC):

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        self.registry = svc_registry
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
        self._routes.append(Route('/kmsKeys', self.get_all_kms_keys, ["GET"]))
        self._routes.append(Route('/decrypt', self.decrypt, ["POST"]))

    @Controller.build_response
    def get_config_names(self, refresh: bool = False) -> dict[str, list[str]]:
        req_filter = self.get_param('filter', required=False)
        if req_filter:
            return {'names': list(self._cfg(refresh).get_parameter_names_by_filter(req_filter))}
        else:
            return {'names': list(self._cfg(refresh).get_parameter_names())}

    @Controller.build_response
    def get_browse_tree(self, refresh: bool = False) -> ConfigOrchard:
        tree = self._cfg_view(refresh).get_config_orchard()
        return tree

    @Controller.build_response
    def get_config(self, refresh: bool = False) -> Union[Fig, FiggyResponse]:
        name = self.get_param('name')
        type = self.get_param('type')
        version = int(self.get_param('version', default=0, required=False))

        if type == 'full':
            fig = self._cfg(refresh).get_fig(name, version=version)
        elif type == 'simple':
            fig = self._cfg(refresh).get_fig_simple(name)
        else:
            fig = self._cfg(refresh).get_fig(name, version=version)

        if fig.is_missing():
            return FiggyResponse.fig_missing()
        else:
            return fig

    @Controller.build_response
    def is_encrypted(self, refresh: bool = False):
        name = self.get_param('name')
        return {'is_encrypted': self._cfg(refresh).is_encrypted(name)}

    @Controller.build_response
    def is_repl_source(self, refresh: bool = False):
        name = self.get_param('name')
        return {'is_repl_source': self._cfg(refresh).is_replication_source(name)}

    @Controller.build_response
    def is_repl_dest(self, refresh: bool = False):
        name = self.get_param('name')
        return {'is_repl_dest': self._cfg(refresh).is_replication_destination(name)}

    @Controller.build_response
    def save_fig(self, refresh: bool = False):
        payload: Dict = request.json
        fig: Fig = Fig(**payload)
        self._cfg(refresh).save(fig)

    @Controller.client_cache(seconds=30)
    @Controller.build_response
    def get_replication_key(self, refresh: bool = False):
        return {'kms_key_id': self._cfg(refresh).get_replication_key()}

    @Controller.client_cache(seconds=30)
    @Controller.build_response
    def get_replication_source(self, refresh: bool = False):
        name = self.get_param('name')
        cfg = self._cfg(refresh).get_replication_config(name)
        return {'source': cfg.source if cfg else None}

    @Controller.build_response
    def delete_fig(self, refresh: bool = False):
        name = self.get_param('name')
        self._cfg(refresh).delete(name)

    @Controller.build_response
    def get_replication_destinations(self, refresh: bool = False) -> List[ReplicationConfig]:
        source = self.get_param('name')

        return self._cfg(refresh).get_replication_configs_by_source(source)

    @Controller.build_response
    def get_replication_config(self, refresh: bool = False):
        source = self.get_param('name')

        return self._cfg(refresh).get_replication_config(source)

    @Controller.build_response
    def get_all_kms_keys(self, refresh: bool = False):
        return self._cfg(refresh).get_all_encryption_keys()

    @Controller.build_response
    def decrypt(self, refresh: bool = False):
        # Todo add generic payload validation
        payload: Dict = request.json
        parameter_name: str = payload.get('parameter_name')
        encrypted_str = payload.get('encrypted_string')

        return {'decrypted_value': self._cfg(refresh).decrypt(parameter_name, encrypted_str)}
