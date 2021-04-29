import logging
from functools import lru_cache
from typing import Set, List, Dict, Union, Optional

import cachetools.func
from figgy.data.dao.usage_tracker import UsageTrackerDao
from figgy.data.dao.user_cache import UserCacheDao
from figgy.models.audit_log import AuditLog
from figgy.models.usage_log import UsageLog

from figcli.models.kms_key import KmsKey
from figcli.svcs.audit import AuditService
from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config import ConfigService
from figcli.svcs.kms import KmsService
from figcli.ui.models.user_log import UserLog
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class UsageTrackingService:

    def __init__(self, usage_tracker_dao: UsageTrackerDao,
                 audit_svc: AuditService,
                 user_cache_dao: UserCacheDao,
                 cfg_svc: ConfigService,
                 kms_svc: KmsService,
                 cache_mgr: CacheManager):
        self._usage = usage_tracker_dao
        self._user = user_cache_dao
        self._cfg = cfg_svc
        self._audit = audit_svc
        self._kms = kms_svc
        self.cache_mgr = cache_mgr
        self.KMS_KEYS = self._cfg.get_all_encryption_keys()

    @cachetools.func.ttl_cache(maxsize=10, ttl=20)
    def get_usage_logs(self, not_retrieved_since: int, filter: str = None) -> List[UsageLog]:

        old_names: Dict[UsageLog] = {}
        new_names: Dict[UsageLog] = {}

        # Find old names, if you find 2 logs with the same name, keep the latest log.
        # This is using a generator so it is 'O'n time complexity.

        for usage_log in self._usage.find_logs_by_time(before=not_retrieved_since, filter=filter):
            if usage_log > old_names.get(usage_log, 0):
                old_names[usage_log] = usage_log

        for usage_log in self._usage.find_logs_by_time(after=not_retrieved_since, filter=filter):
            if usage_log > new_names.get(usage_log, 0):
                new_names[usage_log] = usage_log

        old_names_set: Set[UsageLog] = set(old_names.values())
        new_names_set: Set[UsageLog] = set(new_names.values())
        log.info(f'Found old log names: {old_names_set} and new names: {new_names_set}')
        stale_fig_logs = list(old_names_set - new_names_set)

        # Remove logs for any Figs that have already been deleted.
        active_parameters = self._cfg.get_parameter_names()

        # All figs that have been retrieved at least once and are still active.
        stale_fig_logs = [stale_log for stale_log in stale_fig_logs if stale_log.parameter_name in active_parameters]
        stale_fig_names: Set[str] = set([stale_log.parameter_name for stale_log in stale_fig_logs])

        # Find figs never retrieved but currently active
        never_retrieved = active_parameters.difference(stale_fig_names)
        never_retrieved_logs: List[UsageLog] = [UsageLog.empty(name) for name in never_retrieved]

        if filter:
            never_retrieved_logs = [l for l in never_retrieved_logs if Utils.property_matches(l, filter)]

        return stale_fig_logs + never_retrieved_logs

    @cachetools.func.ttl_cache(maxsize=50, ttl=20)
    def get_user_activity(self, user: str) -> List[UserLog]:
        # Todo fix naming inconsistencies here
        audit_logs: List[AuditLog] = self._audit.get_audit_logs_by_user(user, latest=False)
        usage_logs: List[UsageLog] = list(self._usage.find_logs_by_user(user))

        user_audit_logs: List[UserLog] = [self.__to_user_log(audit_log) for audit_log in audit_logs]
        user_usage_logs: List[UserLog] = [self.__to_user_log(usage_log) for usage_log in usage_logs]
        all_logs = user_audit_logs + user_usage_logs

        return sorted(all_logs)

    @cachetools.func.ttl_cache(maxsize=10, ttl=120)
    def get_parameter_activity(self, parameter_name: str) -> List[UserLog]:
        user_usage_log = [self.__to_user_log(usage_log) for usage_log in
                          list(self._usage.find_by_parameter(parameter_name))]

        user_audit_log = [self.__to_user_log(audit_log) for audit_log in
                          list(self._audit.get_parameter_logs(parameter_name))]
        all_logs = user_usage_log + user_audit_log
        return sorted(all_logs)

    @cachetools.func.ttl_cache(maxsize=400, ttl=500)
    def hydrate_user_log(self, user_log: UserLog):
        # If no value present, lookup and decrypt if necessary
        if not user_log.value:
            audit_log = self._audit.get_audit_log_at_time(user_log.parameter, user_log.time)
            if audit_log:
                user_log.key = self.__get_kms_key(audit_log.key_id)

                # If encrypted, decrypt
                if user_log.key:
                    user_log.value = self._cfg.decrypt(user_log.parameter, audit_log.value)
                else:
                    user_log.value = audit_log.value

        # If value present, decrypt if necessary
        else:
            if user_log.key:
                user_log.value = self._cfg.decrypt(user_log.parameter, user_log.value)

        return user_log

    def get_user_list(self) -> List[str]:
        return list(self._user.get_all_users())

    def get_user_usage_logs(self, user: str, filter: str = None) -> List[UsageLog]:
        return list(self._usage.find_logs_by_user(user, filter))

    def __to_user_log(self, log_entry: Union[AuditLog, UsageLog]) -> UserLog:
        if isinstance(log_entry, AuditLog):
            selected_key = self.__get_kms_key(log_entry.key_id)
            return UserLog(user=log_entry.user,
                           action=log_entry.action,
                           parameter=log_entry.parameter_name,
                           value=log_entry.value,
                           time=log_entry.time,
                           key=selected_key)

        elif isinstance(log_entry, UsageLog):
            return UserLog(user=log_entry.user,
                           action=log_entry.action,
                           parameter=log_entry.parameter_name,
                           time=log_entry.last_updated)

    @lru_cache(maxsize=10)
    def __get_kms_key(self, key_id: str) -> Optional[KmsKey]:
        found_key = [kms_key for kms_key in self.KMS_KEYS if kms_key.id == key_id]
        return found_key[0] if found_key else None

    def __decrypt(self, parameter_name: str, value: str, key: KmsKey) -> str:
        if key:
            return self._kms.safe_decrypt_parameter(parameter_name, value)
        else:
            return value
