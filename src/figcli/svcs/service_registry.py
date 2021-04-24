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
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


def refreshable_cache(cache_key):
    """
    Decorator to support dynamic caching of registered services with a 'refresh'
    parameter that will purge the cache and force refresh of cached services.
    """

    def decorate(method):
        @wraps(method)
        def impl(self, env: GlobalEnvironment, refresh: bool = False):
            if not self.CACHE.get(env, {}).get(cache_key) or refresh:
                log.info(f"Refreshing {cache_key} due to refresh parameter.")
                self.CACHE[env] = self.CACHE.get(env, {}) | {cache_key: method(self, env, refresh)}

            return self.CACHE[env][cache_key]

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

    def init_env(self, env: GlobalEnvironment, mfa: Optional[str] = None):
        log.info(f'Initializing session for role: {env.role.role_arn}, region: {env.region} and MFA: {mfa}')
        self.session_mgr.get_session(env, prompt=False, mfa=mfa)

    def auth_roles(self, envs: List[GlobalEnvironment], mfa: Optional[str] = None):
        for env in envs:
            self.init_env(env, mfa)

    @refreshable_cache('audit-svc')
    def audit_svc(self, env: GlobalEnvironment, refresh: bool = False) -> AuditService:
        return AuditService(self.__audit(env, refresh), self.config_svc(env, refresh),
                            self.kms_svc(env, refresh), self.__cache_mgr(env))

    @refreshable_cache('usage-svc')
    def usage_svc(self, env: GlobalEnvironment, refresh: bool = False) -> UsageTrackingService:
        return UsageTrackingService(self.__usage(env, refresh), self.audit_svc(env, refresh),
                                    self.__user(env, refresh), self.config_svc(env, refresh),
                                    self.kms_svc(env, refresh), self.__cache_mgr(env))

    @refreshable_cache('config-svc')
    def config_svc(self, env: GlobalEnvironment, refresh: bool = False) -> ConfigService:
        """
        Returns a hydrated ConfigSvc
        """
        return ConfigService(self.__config(env, refresh), self.__ssm(env, refresh), self.__repl(env, refresh),
                             self.__cache_mgr(env), self.kms_svc(env, refresh), env.role.run_env)

    @refreshable_cache('kms-svc')
    def kms_svc(self, env: GlobalEnvironment, refresh: bool = False) -> KmsService:
        """
        Returns a hydrated KmsService
        """
        return KmsService(self.__kms(env, refresh), self.__ssm(env, refresh))

    @refreshable_cache('rbac-view')
    def rbac_view(self, env: GlobalEnvironment, refresh: bool = False) -> RBACLimitedConfigView:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        return RBACLimitedConfigView(role=env.role.role,
                                     cache_mgr=self.__cache_mgr(env),
                                     ssm=self.__ssm(env, refresh),
                                     config_svc=self.config_svc(env, refresh),
                                     profile=env.role.profile)

    @refreshable_cache('cache-mgr')
    def __cache_mgr(self, env: GlobalEnvironment, refresh: bool = False):
        return CacheManager(f'{env.cache_key()}')

    @refreshable_cache('env-session')
    def __env_session(self, env: GlobalEnvironment, refresh: bool = False) -> boto3.session.Session:
        """
        Lazy load an ENV session object for the ENV selected in the FiggyContext
        :return: Hydrated session for the selected environment.
        """
        return self.session_mgr.get_session(env, prompt=False)

    @refreshable_cache('ssm-dao')
    def __ssm(self, env: GlobalEnvironment, refresh: bool) -> SsmDao:
        """
        Returns an SSMDao initialized with a session for the selected ENV based on FiggyContext
        """
        return SsmDao(self.__env_session(env, refresh).client('ssm'))

    @refreshable_cache('kms-dao')
    def __kms(self, env: GlobalEnvironment, refresh: bool) -> KmsDao:
        """
        Returns a hydrated KMS Service object based on these selected ENV
        """
        return KmsDao(self.__env_session(env, refresh).client('kms'))

    @refreshable_cache('config-dao')
    def __config(self, env: GlobalEnvironment, refresh: bool) -> ConfigDao:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        return ConfigDao(self.__env_session(env, refresh).resource('dynamodb'))

    @refreshable_cache('audit-dao')
    def __audit(self, env: GlobalEnvironment, refresh: bool) -> AuditDao:
        """
        Returns a hydrated AuditDao for the selected environment.
        """
        return AuditDao(self.__env_session(env, refresh).resource('dynamodb'))

    @refreshable_cache('usage-dao')
    def __usage(self, env: GlobalEnvironment, refresh: bool) -> UsageTrackerDao:
        """
        Returns a hydrated UsageTrackerDao for the selected environment.
        """
        return UsageTrackerDao(self.__env_session(env, refresh).resource('dynamodb'))

    @refreshable_cache('repl-dao')
    def __repl(self, env: GlobalEnvironment, refresh: bool) -> ReplicationDao:
        """
        Returns a hydrated ReplicationDao for the selected environment.
        """
        return ReplicationDao(self.__env_session(env, refresh).resource('dynamodb'))

    @refreshable_cache('user-dao')
    def __user(self, env: GlobalEnvironment, refresh: bool) -> UserCacheDao:
        """
        Returns a hydrated ReplicationDao for the selected environment.
        """
        return UserCacheDao(self.__env_session(env, refresh).resource('dynamodb'))
