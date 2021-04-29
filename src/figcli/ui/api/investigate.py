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
from figcli.ui.models.user_log import UserLog
from figcli.ui.route import Route
from figcli.utils.utils import Utils
from multiprocessing.pool import ThreadPool

log = logging.getLogger(__name__)


class InvestigateController(Controller, ABC):
    MAX_THREADS = 20

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        self._routes.append(Route('/user-logs', self.get_user_logs, ["GET"]))
        self._routes.append(Route('/parameter-logs', self.get_parameter_logs, ["GET"]))

    @Utils.trace
    @Controller.client_cache(seconds=5)
    @Controller.build_response
    def get_user_logs(self, refresh: bool = False) -> PaginatedResponse:
        page: int = int(self.get_param('page', default=0, required=False))
        size: int = int(self.get_param('size', default=15))
        sort_key: str = self.get_param('sort-key', default='time')
        sort_direction: str = self.get_param('sort-direction', default='asc')
        before: int = self.get_param('before', required=False)
        user: str = self.get_param('user', required=True)
        filter: str = self.get_param('filter', required=False)  # by default filter by date.

        matching_logs: List[UserLog] = self._usage(refresh).get_user_activity(user)

        if before:
            matching_logs = [l for l in matching_logs if l.time < before]

        if filter:
            # If filter is applied, use multiple threads to lookup values to match by.
            with ThreadPool(processes=self.MAX_THREADS) as pool:
                futures = []
                for user_log in matching_logs:
                    futures.append(pool.apply_async(self._usage().hydrate_user_log, args=(user_log,)))

                matching_logs = [f.get() for f in futures]

            matching_logs = [l for l in matching_logs if Utils.property_matches(l, filter)]

        sorted_logs = sorted(matching_logs, key=lambda x: x.__dict__.get(sort_key),
                             reverse=False if sort_direction == 'asc' else True)

        sorted_page = sorted_logs[page * size: page * size + size]
        total = len(matching_logs)

        # Now that we have the page, hydrate values.
        sorted_page = [self._usage().hydrate_user_log(user_log) for user_log in sorted_page]

        return PaginatedResponse(data=sorted_page, total=total, page_size=size, page_number=page)

    @Utils.trace
    @Controller.client_cache(seconds=5)
    @Controller.build_response
    def get_parameter_logs(self, refresh: bool = False) -> PaginatedResponse:
        page: int = int(self.get_param('page', default=0, required=False))
        size: int = int(self.get_param('size', default=15))
        sort_key: str = self.get_param('sort-key', default='time')
        sort_direction: str = self.get_param('sort-direction', default='asc')
        before: int = self.get_param('before', required=False)
        parameter: str = self.get_param('name', required=True)
        filter: str = self.get_param('filter', required=False)  # by default filter by date.

        matching_logs: List[UserLog] = self._usage(refresh).get_parameter_activity(parameter)
        log.info(f'Got matching logs {matching_logs}')
        if before:
            matching_logs = [l for l in matching_logs if l.time < before]

        if filter:
            # If filter is applied, use multiple threads to lookup values to match by.
            with ThreadPool(processes=self.MAX_THREADS) as pool:
                futures = []
                for user_log in matching_logs:
                    futures.append(pool.apply_async(self._usage().hydrate_user_log, args=(user_log,)))

                matching_logs = [f.get() for f in futures]

            matching_logs = [l for l in matching_logs if Utils.property_matches(l, filter)]

        sorted_logs = sorted(matching_logs, key=lambda x: x.__dict__.get(sort_key),
                             reverse=False if sort_direction == 'asc' else True)

        sorted_page = sorted_logs[page * size: page * size + size]
        total = len(matching_logs)

        # Now that we have the page, hydrate values.
        sorted_page = [self._usage().hydrate_user_log(user_log) for user_log in sorted_page]

        return PaginatedResponse(data=sorted_page, total=total, page_size=size, page_number=page)
