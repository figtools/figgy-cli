import logging
from functools import wraps

import boto3

from typing import Dict, Optional, List

from figgy.data.dao.audit import AuditDao
from figgy.data.dao.config import ConfigDao
from figgy.data.dao.kms import KmsDao
from figgy.data.dao.replication import ReplicationDao
from figgy.data.dao.ssm import SsmDao
from figgy.data.dao.usage_tracker import UsageTrackerDao
from figgy.data.dao.user_cache import UserCacheDao

from figcli.commands.command_context import CommandContext
from figcli.models.assumable_role import AssumableRole
from figcli.svcs.audit import AuditService
from figcli.svcs.auth.session_manager import SessionManager
from threading import Lock

from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config import ConfigService
from figcli.svcs.kms import KmsService
from figcli.svcs.usage_tracking import UsageTrackingService
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


def refreshable_cache(cache_key):
    """
    Decorator to support dynamic caching of registered services with a 'refresh'
    parameter that will purge the cache and force refresh of cached services.
    """

    def decorate(method):
        @wraps(method)
        def impl(self, role: AssumableRole, refresh: bool = False):
            if not self.CACHE.get(role, {}).get(cache_key) or refresh:
                log.info(f"Refreshing {cache_key} due to refresh parameter.")
                self.CACHE[role] = self.CACHE.get(role, {}) | {cache_key: method(self, role, refresh)}

            return self.CACHE[role][cache_key]

        return impl

    return decorate


class ServiceRegistry:
    CACHE: Dict = {}

    def __init__(self, session_mgr: SessionManager, context: CommandContext):
        self.session_mgr = session_mgr
        self.context = context
        self.__env_lock = Lock()
        self.__mgr_lock = Lock()

    # Todo Decorate / cleanup caching situation, lots of duplication here.

    def init_role(self, role: AssumableRole, mfa: Optional[str] = None):
        log.info(f'Initializing session for role: {role.role_arn} and MFA: {mfa}')
        self.session_mgr.get_session(role, prompt=False, mfa=mfa)

    def auth_roles(self, roles: List[AssumableRole], mfa: Optional[str] = None):
        for role in roles:
            self.init_role(role, mfa)

    @refreshable_cache('audit-svc')
    def audit_svc(self, role: AssumableRole, refresh: bool = False) -> AuditService:
        return AuditService(self.__audit(role, refresh), self.config_svc(role, refresh),
                            self.kms_svc(role, refresh), self.__cache_mgr(role))

    @refreshable_cache('usage-svc')
    def usage_svc(self, role: AssumableRole, refresh: bool = False) -> UsageTrackingService:
        return UsageTrackingService(self.__usage(role, refresh), self.audit_svc(role, refresh),
                                    self.__user(role, refresh), self.config_svc(role, refresh),
                                    self.kms_svc(role, refresh), self.__cache_mgr(role))

    @refreshable_cache('config-svc')
    def config_svc(self, role: AssumableRole, refresh: bool = False) -> ConfigService:
        """
        Returns a hydrated ConfigSvc
        """
        return ConfigService(self.__config(role, refresh), self.__ssm(role, refresh), self.__repl(role, refresh),
                             self.__cache_mgr(role), self.kms_svc(role, refresh), role.run_env)

    @refreshable_cache('kms-svc')
    def kms_svc(self, role: AssumableRole, refresh: bool = False) -> KmsService:
        """
        Returns a hydrated KmsService
        """
        return KmsService(self.__kms(role, refresh), self.__ssm(role, refresh))

    @refreshable_cache('rbac-view')
    def rbac_view(self, role: AssumableRole, refresh: bool = False) -> RBACLimitedConfigView:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        return RBACLimitedConfigView(role=role.role,
                                     cache_mgr=self.__cache_mgr(role),
                                     ssm=self.__ssm(role, refresh),
                                     config_svc=self.config_svc(role, refresh),
                                     profile=role.profile)

    @refreshable_cache('cache-mgr')
    def __cache_mgr(self, role: AssumableRole, refresh: bool = False):
        return CacheManager(f'{role.role}-{role.run_env}-{role.account_id[-4:]}')

    @refreshable_cache('env-session')
    def __env_session(self, role: AssumableRole, refresh: bool = False) -> boto3.session.Session:
        """
        Lazy load an ENV session object for the ENV selected in the FiggyContext
        :return: Hydrated session for the selected environment.
        """
        return self.session_mgr.get_session(role, prompt=False)

    @refreshable_cache('ssm-dao')
    def __ssm(self, role: AssumableRole, refresh: bool) -> SsmDao:
        """
        Returns an SSMDao initialized with a session for the selected ENV based on FiggyContext
        """
        return SsmDao(self.__env_session(role, refresh).client('ssm'))

    @refreshable_cache('kms-dao')
    def __kms(self, role: AssumableRole, refresh: bool) -> KmsDao:
        """
        Returns a hydrated KMS Service object based on these selected ENV
        """
        return KmsDao(self.__env_session(role, refresh).client('kms'))

    @refreshable_cache('config-dao')
    def __config(self, role: AssumableRole, refresh: bool) -> ConfigDao:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        return ConfigDao(self.__env_session(role, refresh).resource('dynamodb'))

    @refreshable_cache('audit-dao')
    def __audit(self, role: AssumableRole, refresh: bool) -> AuditDao:
        """
        Returns a hydrated AuditDao for the selected environment.
        """
        return AuditDao(self.__env_session(role, refresh).resource('dynamodb'))

    @refreshable_cache('usage-dao')
    def __usage(self, role: AssumableRole, refresh: bool) -> UsageTrackerDao:
        """
        Returns a hydrated UsageTrackerDao for the selected environment.
        """
        return UsageTrackerDao(self.__env_session(role, refresh).resource('dynamodb'))

    @refreshable_cache('repl-dao')
    def __repl(self, role: AssumableRole, refresh: bool) -> ReplicationDao:
        """
        Returns a hydrated ReplicationDao for the selected environment.
        """
        return ReplicationDao(self.__env_session(role, refresh).resource('dynamodb'))

    @refreshable_cache('user-dao')
    def __user(self, role: AssumableRole, refresh: bool) -> UserCacheDao:
        """
        Returns a hydrated ReplicationDao for the selected environment.
        """
        return UserCacheDao(self.__env_session(role, refresh).resource('dynamodb'))
