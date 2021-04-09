import logging
from typing import List

from figgy.data.dao.config import ConfigDao
from figgy.models.audit_log import AuditLog

from figcli.svcs.cache_manager import CacheManager

log = logging.getLogger(__name__)


class AuditService:

    def __init__(self, cfg_dao: ConfigDao, cache_mgr: CacheManager):
        self._cfg = cfg_dao
        self.cache_mgr = cache_mgr

    def get_unrotated_secrets(self, not_rotated_since: int, filter: str = None) -> List[str]:
        stale_cfgs: List[AuditLog] = self._cfg.get_unrotated_configs(not_rotated_since, filter=filter, secrets_only=True)

        log.info(f'Found stale configs {stale_cfgs}')

        return [cfg.parameter_name for cfg in stale_cfgs]

    def get_unrotated_audit_logs(self, not_rotated_since: int, filter: str) -> List[AuditLog]:
        return self._cfg.get_unrotated_configs(not_rotated_since, filter=filter, secrets_only=True)
