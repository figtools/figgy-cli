import json
import logging
from functools import wraps

import boto3
import time

from typing import Dict, Optional, List

from figgy.data.dao.audit import AuditDao
from figgy.data.dao.config import ConfigDao
from figgy.data.dao.kms import KmsDao
from figgy.data.dao.replication import ReplicationDao
from figgy.data.dao.ssm import SsmDao
from figgy.data.dao.usage_tracker import UsageTrackerDao
from figgy.data.dao.user_cache import UserCacheDao
from figgy.models.fig import Fig
from figgy.models.run_env import RunEnv
from filelock import FileLock

from figcli.commands.command_context import CommandContext
from figcli.config import BOTO3_CLIENT_FILE_LOCK_PATH, PS_FIGGY_ENV_ALIAS, PS_FIGGY_UTILITY_ACCOUNT_ID, \
    PS_FIGGY_CURRENT_ACCOUNT_ID, PS_FIGGY_OTS_KEY_ID, PS_FIGGY_REGIONS, FIGGY_DEFAULT_ROLE_NAME
from figcli.config.tuning import DYNAMO_DB_MAX_POOL_SIZE, MAX_CACHED_BOTO_POOLS
from figcli.models.assumable_role import AssumableRole
from figcli.models.role import Role
from figcli.svcs.audit import AuditService
from figcli.svcs.auth.session_manager import SessionManager
from botocore.client import Config

from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config import ConfigService
from figcli.svcs.kms import KmsService
from figcli.svcs.one_time_secret import OTSService
from figcli.svcs.usage_tracking import UsageTrackingService
from figcli.ui.exceptions import InvalidFiggyConfigurationException
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.utils.utils import Utils
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


def refreshable_cache(cache_key):
    """
    Decorator to support dynamic caching of registered services with a 'refresh'
    parameter that will purge the cache and force refresh of cached services.
    """

    def decorate(method):
        """
        Stores initialized services in an in-memory cache. Services are cached by ENV and REGION. Due to
        issues with @cachetools that I have still not entirely figured out, methods cached with @cachetools decorators
        cause boto3 connection pools to evade garbage collection. To address this issue, we are purging this cache as
        we get to an estimated MAX_CACHED_BOTO_POOLS number of connection pools. Purging this cache is not enough as
        GC will not clean up the connection pools unless all methods cached by @cachetools have their clear_cache()
        method executed. This decorator will forceably purge all method-level caches when this service cache is purged,
        thereby allowing garbage collection to clean up the boto connection pools and prevent figgy from maintaining
        too many open files and potentially approaching ulimits on some systems.
        """

        @wraps(method)
        def impl(self, env: GlobalEnvironment, refresh: bool = False):
            if not self.CACHE.get(env, {}).get(cache_key) or refresh:
                while len(self.CACHE) > MAX_CACHED_BOTO_POOLS:
                    sorted_items = sorted(self.CACHE.items(), key=lambda x: x[1]['last_set'])
                    oldest_item = sorted_items[0]
                    log.info(f'Removing from cache: {oldest_item[0]}')
                    for key, value in self.CACHE[oldest_item[0]].items():
                        object_methods = [func for func in dir(value) if callable(getattr(value, func))
                                          and not func.startswith('__')]

                        for func in object_methods:
                            try:
                                log.info(f'Clearing cache for method: {func}')
                                this_func = getattr(value, func)
                                this_func.cache_clear()
                            except Exception as e:
                                log.info(f'Caught expected exception: {e} when attempting cache clear for method {func}')

                    try:
                        self.CACHE.pop(oldest_item[0])
                    except KeyError:
                        log.info(f'Cache key already removed, passing..')
                        pass

                self.CACHE[env] = self.CACHE.get(env, {}) | {cache_key: method(self, env, refresh)}
                self.CACHE[env] = self.CACHE.get(env, {}) | {'last_set': time.time()}

            return self.CACHE[env][cache_key]

        return impl

    return decorate


def lock_boto_client_creation(method):
    """
    Locks boto client creationa cross threads to prevent occasional error messages due to non-thread safe nature of botoclient
    creation.
    """

    @wraps(method)
    def impl(self, *args, **kwargs):
        with FileLock(BOTO3_CLIENT_FILE_LOCK_PATH):
            log.info(f"Locking: {BOTO3_CLIENT_FILE_LOCK_PATH} for method: {method.__name__}")
            return method(self, *args, **kwargs)

    return impl


class ServiceRegistry:
    CACHE: Dict = {}

    def __init__(self, session_mgr: SessionManager, context: CommandContext):
        self.session_mgr = session_mgr
        self.context = context

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

    @Utils.trace
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

    @Utils.trace
    @refreshable_cache('ots-svc')
    def ots_svc(self, env: GlobalEnvironment, refresh: bool = False) -> OTSService:
        """
        Returns a hydrated & properly configured One-time-secret service. This service will be configured for the appropriate
        "utility" account by the registry.
        """

        new_env = env

        try:
            config_svc = self.config_svc(env=env, refresh=refresh)
            utility_account_id: Fig = config_svc.get_fig_with_cache(PS_FIGGY_UTILITY_ACCOUNT_ID).value
            log.debug(f"Got utility account id: {utility_account_id}")
            current_account_id: Fig = config_svc.get_fig_with_cache(PS_FIGGY_CURRENT_ACCOUNT_ID).value
            log.debug(f"Got current session alias: {current_account_id}")
            new_role = Role(role=FIGGY_DEFAULT_ROLE_NAME, full_name='figgy-default')
            regions = config_svc.get_fig_with_cache(PS_FIGGY_REGIONS)
            ots_region = json.loads(regions.value)[0]

            new_env = GlobalEnvironment(role=AssumableRole(account_id=utility_account_id,
                                                           run_env=RunEnv(env="utility", account_id=utility_account_id),
                                                           role=new_role,
                                                           provider_name=env.role.provider_name),
                                        region=ots_region)
        except BaseException as e:
            raise InvalidFiggyConfigurationException(f"Unable to initialize one-time-secret service. Are you sure your "
                                                     f"'utility_account_alias' was set to a valid value when you configured "
                                                     f"Figgy Cloud?") from e

        config_svc = self.config_svc(env=new_env, refresh=refresh)
        ots_key: Fig = config_svc.get_fig_with_cache(PS_FIGGY_OTS_KEY_ID)

        return OTSService(self.__ssm(env=new_env, refresh=refresh),
                          self.__kms(env=new_env, refresh=refresh),
                          kms_id=ots_key.value)

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

    @Utils.trace
    @refreshable_cache('ssm-dao')
    @lock_boto_client_creation
    def __ssm(self, env: GlobalEnvironment, refresh: bool) -> SsmDao:
        """
        Returns an SSMDao initialized with a session for the selected ENV based on FiggyContext
        """
        return SsmDao(self.__env_session(env, refresh).client('ssm'))

    @Utils.trace
    @refreshable_cache('kms-dao')
    @lock_boto_client_creation
    def __kms(self, env: GlobalEnvironment, refresh: bool) -> KmsDao:
        """
        Returns a hydrated KMS Service object based on these selected ENV
        """
        return KmsDao(self.__env_session(env, refresh).client('kms'))

    @refreshable_cache('config-dao')
    @lock_boto_client_creation
    def __config(self, env: GlobalEnvironment, refresh: bool) -> ConfigDao:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        return ConfigDao(self.__env_session(env, refresh).resource('dynamodb'))

    @refreshable_cache('audit-dao')
    @lock_boto_client_creation
    def __audit(self, env: GlobalEnvironment, refresh: bool) -> AuditDao:
        """
        Returns a hydrated AuditDao for the selected environment.
        """
        return AuditDao(self.__env_session(env, refresh)
                        .resource('dynamodb', config=Config(max_pool_connections=DYNAMO_DB_MAX_POOL_SIZE)))

    @refreshable_cache('usage-dao')
    @lock_boto_client_creation
    def __usage(self, env: GlobalEnvironment, refresh: bool) -> UsageTrackerDao:
        """
        Returns a hydrated UsageTrackerDao for the selected environment.
        """
        return UsageTrackerDao(self.__env_session(env, refresh)
                               .resource('dynamodb', config=Config(max_pool_connections=DYNAMO_DB_MAX_POOL_SIZE)))

    @refreshable_cache('repl-dao')
    @lock_boto_client_creation
    def __repl(self, env: GlobalEnvironment, refresh: bool) -> ReplicationDao:
        """
        Returns a hydrated ReplicationDao for the selected environment.
        """
        return ReplicationDao(self.__env_session(env, refresh)
                              .resource('dynamodb', config=Config(max_pool_connections=DYNAMO_DB_MAX_POOL_SIZE)))

    @refreshable_cache('user-dao')
    @lock_boto_client_creation
    def __user(self, env: GlobalEnvironment, refresh: bool) -> UserCacheDao:
        """
        Returns a hydrated ReplicationDao for the selected environment.
        """
        return UserCacheDao(self.__env_session(env, refresh)
                            .resource('dynamodb', config=Config(max_pool_connections=DYNAMO_DB_MAX_POOL_SIZE)))
