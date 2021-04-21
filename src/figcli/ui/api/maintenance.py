import logging
from abc import ABC
from typing import List

from figgy.models.audit_log import AuditLog

from figcli.commands.command_context import CommandContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.paginated_response import PaginatedResponse
from figcli.ui.route import Route
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class MaintenanceController(Controller, ABC):

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        self._routes.append(Route('/unrotated-secrets', self.get_unrotated_secrets, ["GET"]))

    @Utils.trace
    @Controller.client_cache(seconds=5)
    @Controller.build_response
    def get_unrotated_secrets(self, refresh: bool = False) -> PaginatedResponse:
        page: int = int(self.get_param('page', default=0, required=False))
        size: int = int(self.get_param('size', default=15))
        filter: str = self.get_param('filter', required=False)  # by default filter by date.
        sort_key: str = self.get_param('sort-key', default='time')
        sort_direction: str = self.get_param('sort-direction', default='asc')
        before: int = self.get_param('before', required=False)

        matching_logs: List[AuditLog] = self._audit(refresh).get_unrotated_secret_logs(filter=filter, before=before)
        sorted_logs = sorted(matching_logs, key=lambda x: x.__dict__.get(sort_key),
                             reverse=False if sort_direction == 'asc' else True)

        sorted_page = sorted_logs[page * size: page * size + size]
        total = len(matching_logs)

        return PaginatedResponse(data=sorted_page, total=total, page_size=size, page_number=page)
