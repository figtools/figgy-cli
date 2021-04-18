import logging
from typing import Set, List, Dict

from figgy.data.dao.config import ConfigDao
from figgy.data.dao.usage_tracker import UsageTrackerDao
from figgy.models.usage_log import UsageLog

from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config import ConfigService
from figcli.svcs.kms import KmsSvc

log = logging.getLogger(__name__)


class UsageTrackingService:

    def __init__(self, usage_tracker_dao: UsageTrackerDao,
                 cfg_svc: ConfigService,
                 kms_svc: KmsSvc,
                 cache_mgr: CacheManager):
        self._usage = usage_tracker_dao
        self._cfg = cfg_svc
        self._kms = kms_svc
        self.cache_mgr = cache_mgr

    def get_stale_figs(self, not_retrieved_since: int, filter: str = None) -> List[UsageLog]:

        old_names: Dict[UsageLog] = {}
        new_names: Dict[UsageLog] = {}

        # Find old names, if you find 2 logs with the same name, keep the latest log.
        # This is using a generator so it is 'O'n time complexity.

        for usage_logs in self._usage.find_logs_by_time(before=not_retrieved_since, filter=filter):
            for usage_log in usage_logs:
                if usage_log > old_names.get(usage_log, 0):
                    old_names[usage_log] = usage_log

        for usage_logs in self._usage.find_logs_by_time(after=not_retrieved_since, filter=filter):
            for usage_log in usage_logs:
                if usage_log > new_names.get(usage_log, 0):
                    new_names[usage_log] = usage_log

        old_names_set: Set[UsageLog] = set(old_names.values())
        new_names_set: Set[UsageLog] = set(new_names.values())
        log.info(f'Found old log names: {old_names_set} and new names: {new_names_set}')
        stale_fig_logs = list(old_names_set - new_names_set)

        # Remove logs for any Figs that have already been deleted.
        active_parameters = self._cfg.get_parameter_names()
        stale_fig_logs = [stale_log for stale_log in stale_fig_logs if stale_log.parameter_name in active_parameters]

        return stale_fig_logs
