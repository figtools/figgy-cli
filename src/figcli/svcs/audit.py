import logging
from concurrent.futures.thread import ThreadPoolExecutor
from multiprocessing.pool import ThreadPool
from typing import List

from cachetools import TTLCache, cached, LRUCache
from figgy.constants.data import SSM_DELETE, SSM_SECURE_STRING
from figgy.data.dao.audit import AuditDao
from figgy.models.audit_log import AuditLog

from figcli.models.audit_log_details import AuditLogDetails
from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config import ConfigService
from figcli.svcs.kms import KmsService

log = logging.getLogger(__name__)


class AuditService:
    MAX_THREADS = 10

    def __init__(self, audit_dao: AuditDao, cfg_svc: ConfigService, kms_svc: KmsService, cache_mgr: CacheManager):
        self._audit = audit_dao
        self._cfg = cfg_svc
        self._kms = kms_svc
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
        result = self._audit.find_logs_parallel(threads=self.MAX_THREADS, filter=filter,
                                                parameter_type=parameter_type, before=before,
                                                after=after)

        return result

    @cached(TTLCache(maxsize=10, ttl=30))
    def get_audit_logs_by_user(self, user: str, latest=False) -> List[AuditLog]:
        return self._audit.find_by_user(user, latest=latest)

    @cached(TTLCache(maxsize=100, ttl=3000))
    def get_audit_log_at_time(self, parameter_name: str, time: int) -> AuditLog:
        return self._audit.get_put_log_before(parameter_name, time)

    @cached(TTLCache(maxsize=5, ttl=30))
    def get_parameter_logs(self, name: str) -> List[AuditLog]:
        return self._audit.get_audit_logs(ps_name=name)

    @cached(TTLCache(maxsize=200, ttl=120))
    def get_audit_log_details(self, parameter_name: str, time: int) -> AuditLogDetails:
        audit_log: AuditLog = self._audit.get_log(parameter_name, time)

        if audit_log.action == SSM_DELETE:
            audit_log.value = self._audit.get_deleted_value(audit_log.parameter_name, audit_log.time)

        decrypted_value = self._kms.safe_decrypt_parameter(audit_log.parameter_name, audit_log.value)
        return AuditLogDetails(**audit_log.dict(), decrypted_value=decrypted_value)

    @cached(TTLCache(maxsize=10, ttl=30))
    def get_unrotated_secret_logs(self, filter: str = None,
                                  before: int = None) -> List[AuditLog]:
        all_logs = self.get_audit_logs_matching(filter=filter, parameter_type=SSM_SECURE_STRING, before=before)

        # Filter out logs from parameters that no longer exist
        active_parameters = self._cfg.get_parameter_names()
        active_logs = [l for l in all_logs if l.parameter_name in active_parameters]

        # Use multiple threads to lookup which parameters are replication destinations and remove them from the
        # log list. Since we are waiting on network, this is many times faster.
        # We cannot use ThreadPoolExecutor due to compatibility issues when running from within a flask request.
        # I have  Todo to dive deeper into this and address these compatibility issues
        pool = ThreadPool(processes=self.MAX_THREADS)
        try:
            futures, repl_dest_params = {}, []
            for l in active_logs:
                thread = pool.apply_async(self._cfg.is_replication_destination, args=(l.parameter_name,))
                futures[l.parameter_name] = thread

            for param_name, future in futures.items():
                if future.get():
                    repl_dest_params.append(param_name)

            # remove destinations:
            active_logs = [l for l in active_logs if l.parameter_name not in repl_dest_params]
        finally:
            pool.close()

        return active_logs
