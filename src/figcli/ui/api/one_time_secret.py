import logging
from abc import ABC
from typing import Dict

from flask import request

from figcli.commands.command_context import CommandContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.figgy_response import FiggyResponse
from figcli.ui.route import Route
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class OTSController(Controller, ABC):

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        self._routes.append(Route('/ots', self.get_ots, ["GET"]))
        self._routes.append(Route('/ots', self.put_ots, ["PUT"]))

    @Utils.trace
    @Controller.build_response
    def get_ots(self, refresh: bool = False):
        secret_id = self.get_param('secretId', default=None, required=False)
        secret_val = self._ots(refresh).get_ots(secret_id)

        if not secret_val:
            return FiggyResponse.ots_missing()

        return {'ots_value': secret_val}

    @Utils.trace
    @Controller.build_response
    def put_ots(self, refresh: bool = False):
        payload: Dict = request.json
        value = payload.get('value')
        expires_in = float(payload.get('expires_in'))
        
        secret_id = self._ots(refresh).put_ots(value, expires_in)

        if not secret_id:
            raise ValueError("One-time-secret storage failure. Please retry.")

        return {'secret_id': secret_id}
