import logging
import sys
import time
from typing import List

from cachetools import TTLCache, cached
from figgy.data.dao.audit import AuditDao
from figgy.data.dao.config import ConfigDao
from figgy.models.audit_log import AuditLog

from figcli.svcs.cache_manager import CacheManager
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class AuditService:

    def __init__(self, audit_dao: AuditDao, cfg_dao: ConfigDao, cache_mgr: CacheManager):
        self._audit = audit_dao
        self._cfg = cfg_dao
        self.cache_mgr = cache_mgr

    @cached(TTLCache(maxsize=5, ttl=30))
    def get_parameters_matching(self, filter: str = None,
                                parameter_type: str = None,
                                before: int = None,
                                after: int = None) -> List[str]:
        logs: List[AuditLog] = self._audit.find_logs(filter=filter, parameter_type=parameter_type, before=before,
                                                     after=after)

        return [cfg.parameter_name for cfg in logs]

    @cached(TTLCache(maxsize=10, ttl=500))
    def get_audit_logs_matching(self, filter: str = None,
                                parameter_type: str = None,
                                before: int = None,
                                after: int = None) -> List[AuditLog]:

        result = self._audit.find_logs_parallel(threads=5, filter=filter, parameter_type=parameter_type, before=before,
                                                after=after)

        return result

    @cached(TTLCache(maxsize=5, ttl=30))
    def get_parameter_logs(self, name: str) -> List[AuditLog]:
        return self._audit.get_audit_logs(ps_name=name)
