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
        self._routes.append(Route('/audit-logs', self.get_audit_logs, ["GET"]))

    # Todo increase cache duration later.
    # @Controller.client_cache(seconds=5)
    # @Controller.build_response
    # def get_unrotated_secrets(self, refresh: bool = False) -> dict[str, list[str]]:
    #     not_rotated_since: int = self.get_param('not-rotated-since', required=True)
    #
    #     results = self._audit(refresh).get_parameters_matching(not_rotated_since=not_rotated_since)
    #
    #     return {'unrotated_figs': results}

    @Controller.client_cache(seconds=5)
    @Controller.build_response
    def get_audit_logs(self, refresh: bool = False) -> PaginatedResponse:
        page: int = int(self.get_param('page', default=0, required=False))
        size: int = int(self.get_param('size', default=15))
        filter: str = self.get_param('filter', required=False)  # by default filter by date.
        sort_key: str = self.get_param('sort-key', default='time')
        sort_direction: str = self.get_param('sort-direction', default='asc')
        before: int = self.get_param('before', required=False)
        after: int = self.get_param('after', required=False)
        parameter_type: str = self.get_param('type', required=False)
        parameter_name: str = self.get_param('name', required=False)

        if parameter_name:
            matching_logs: List[AuditLog] = self._audit(refresh).get_parameter_logs(parameter_name)
        else:
            matching_logs: List[AuditLog] = self._audit(refresh).get_audit_logs_matching(parameter_type=parameter_type,
                                                                                         filter=filter, before=before,
                                                                                         after=after)
        log.info(f"Sorting {sort_direction} by sort_key: {sort_key}")
        sorted_logs = sorted(matching_logs, key=lambda x: x.__dict__.get(sort_key),
                             reverse=False if sort_direction == 'asc' else True)
        log.info(f"Got sorted logs: {sorted_logs}")
        sorted_page = sorted_logs[page * size: page * size + size]
        log.info(f"Got sorted page: {sorted_page}")
        total = len(matching_logs)

        return PaginatedResponse(data=sorted_page, total=total, page_size=size, page_number=page)
