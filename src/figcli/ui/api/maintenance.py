import logging

from abc import ABC
from typing import List

from figgy.models.audit_log import AuditLog

from figcli.commands.command_context import CommandContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.paginated_response import PaginatedResponse
from figcli.ui.route import Route

log = logging.getLogger(__name__)


class MaintenanceController(Controller, ABC):

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        # self._routes.append(Route('/unrotated', self.get_unrotated_secrets, ["GET"]))
        # self._routes.append(Route('/audit-logs', self.get_audit_logs, ["GET"]))

    # Todo increase cache duration later.
    # @Controller.client_cache(seconds=5)
    # @Controller.build_response
    # def get_unrotated_secrets(self, refresh: bool = False) -> dict[str, list[str]]:
    #     not_rotated_since: int = self.get_param('not-rotated-since', required=True)
    #
    #     results = self._audit(refresh).get_parameters_matching(not_rotated_since=not_rotated_since)
    #
    #     return {'unrotated_figs': results}

