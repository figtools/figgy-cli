import logging
from abc import ABC
from typing import List

from figgy.models.audit_log import AuditLog
from figgy.models.usage_log import UsageLog

from figcli.commands.command_context import CommandContext
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.exceptions import BadRequestParameters
from figcli.ui.models.paginated_response import PaginatedResponse
from figcli.ui.route import Route
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class MaintenanceController(Controller, ABC):

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        # self._routes.append(Route('/stale-figs', self.get_stale_figs, ["GET"]))
        self._routes.append(Route('/unrotated-secrets', self.get_unrotated_secrets, ["GET"]))

    # Todo increase cache duration later.
    # @Controller.client_cache(seconds=5)
    # @Controller.build_response
    # def get_stale_figs(self, refresh: bool = False) -> PaginatedResponse:
    #     page: int = int(self.get_param('page', default=0, required=False))
    #     size: int = int(self.get_param('size', default=15))
    #     sort_key: str = self.get_param('sort-key', default='last_updated')
    #     sort_direction: str = self.get_param('sort-direction', default='asc')
    #     not_retrieved_since: int = int(self.get_param('not-retrieved-since', required=True))
    #     filter: str = self.get_param('filter', required=False, default=None)  # by default filter by date.
    #
    #     matching_logs: List[UsageLog] = self._usage(refresh).get_stale_figs(not_retrieved_since=not_retrieved_since,
    #                                                                         filter=filter)
    #     log.info(f'Got page: {page} and size: {size} sorted by {sort_key} / {sort_direction}')
    #     try:
    #         sorted_logs = sorted(matching_logs, key=lambda x: x.__dict__.get(sort_key),
    #                              reverse=False if sort_direction == 'asc' else True)
    #     except AttributeError as e:
    #         raise BadRequestParameters(f'Provided sort_key is not a sortable attribute. '
    #                                    f'Must choose from: {Utils.class_props(UsageLog)}', ['sort_key'])
    #
    #     sorted_page = sorted_logs[page * size: page * size + size]
    #     total = len(matching_logs)
    #
    #     return PaginatedResponse(data=sorted_page, total=total, page_size=size, page_number=page)

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
