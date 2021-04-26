import logging

from abc import ABC
from typing import List, Union

from figgy.models.audit_log import AuditLog

from figcli.commands.command_context import CommandContext
from figcli.models.audit_log_details import AuditLogDetails
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.paginated_response import PaginatedResponse
from figcli.ui.route import Route
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class AuditController(Controller, ABC):
    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        self._routes.append(Route('/logs', self.get_audit_logs, ["GET"]))
        self._routes.append(Route('/logs/details', self.get_audit_details, ["GET"]))

    @Utils.trace
    @Controller.client_cache(seconds=5)
    @Controller.build_response
    def get_audit_logs(self, refresh: bool = False) -> Union[PaginatedResponse, List[AuditLog]]:
        page: int = int(self.get_param('page', default=0, required=False))
        size: int = int(self.get_param('size', default=15))
        filter: str = self.get_param('filter', required=False)  # by default filter by date.
        sort_key: str = self.get_param('sort-key', default='time')
        sort_direction: str = self.get_param('sort-direction', default='asc')
        before: int = self.get_param('before', required=False)
        after: int = self.get_param('after', required=False)
        parameter_type: str = self.get_param('type', required=False)
        parameter_name: str = self.get_param('name', required=False)
        one_page: bool = self.get_param('one-page', required=False, default='false').lower() == 'true'

        if parameter_name:
            matching_logs: List[AuditLog] = self._audit(refresh).get_parameter_logs(parameter_name)
            if filter:
                matching_logs = [l for l in matching_logs if Utils.property_matches(l, filter)]
        else:
            matching_logs: List[AuditLog] = self._audit(refresh).get_audit_logs_matching(parameter_type=parameter_type,
                                                                                         filter=filter, before=before,
                                                                                         after=after)
        sorted_logs = sorted(matching_logs, key=lambda x: x.__dict__.get(sort_key),
                             reverse=False if sort_direction == 'asc' else True)

        sorted_page = sorted_logs[page * size: page * size + size]
        total = len(matching_logs)
        sorted_page = [self._audit().hydrate_audit_log(audit_log) for audit_log in sorted_page]

        if one_page:
            return sorted_logs
        else:
            return PaginatedResponse(data=sorted_page, total=total, page_size=size, page_number=page)


    @Controller.build_response
    def get_audit_details(self, refresh: bool = False) -> AuditLogDetails:
        parameter_name: str = self.get_param('parameter')
        time: int = int(self.get_param('time'))

        details = self._audit(refresh).get_audit_log_details(parameter_name, time)
        return details
