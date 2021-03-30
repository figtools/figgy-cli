import logging
import boto3

from typing import Dict

from figgy.data.dao.config import ConfigDao
from figgy.data.dao.ssm import SsmDao

from figcli.commands.command_context import CommandContext
from figcli.models.assumable_role import AssumableRole
from figcli.svcs.auth.session_manager import SessionManager
from threading import Lock

from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config import ConfigService
from figcli.svcs.kms import KmsSvc
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


class ServiceRegistry:
    CACHE: Dict = {}

    def __init__(self, session_mgr: SessionManager, context: CommandContext):
        self.session_mgr = session_mgr
        self.context = context
        self.__env_lock = Lock()
        self.__mgr_lock = Lock()

    def config_svc(self, role: AssumableRole, refresh: bool = False) -> ConfigService:

        if not self.CACHE.get(role, {}).get('config-svc') or refresh:
            if refresh:
                log.info("Refreshing config-svc due to refresh paramter.")

            self.CACHE[role]['config-svc'] = ConfigService(self.__config(role, refresh), self.__ssm(role, refresh),
                                                           self.__cache_mgr(role), role.run_env)

        return self.CACHE[role]['config-svc']

    def rbac_view(self, role: AssumableRole, refresh: bool = False) -> RBACLimitedConfigView:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        if not self.CACHE.get(role, {}).get('rbac-view') or refresh:
            if refresh:
                log.info("Refreshing RBAC-VIEW due to refresh parameter.")

            self.CACHE[role] = self.CACHE.get(role, {}) | \
                               {'rbac-view': RBACLimitedConfigView(role=role.role,
                                                                   cache_mgr=self.__cache_mgr(role),
                                                                   ssm=self.__ssm(role, refresh),
                                                                   config_svc=self.config_svc(role, refresh),
                                                                   profile=role.profile)}

        return self.CACHE[role]['rbac-view']

    def __cache_mgr(self, role: AssumableRole):
        if not self.CACHE.get(role, {}).get('cache-mgr'):
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'cache-mgr': CacheManager(f'{role.role}-{role.run_env}-{role.account_id[-4:]}')}

        return self.CACHE[role]['cache-mgr']

    def __env_session(self, role: AssumableRole, refresh: bool = False) -> boto3.session.Session:
        """
        Lazy load an ENV session object for the ENV selected in the FiggyContext
        :return: Hydrated session for the selected environment.
        """
        if not self.CACHE.get(role, {}).get('env-session') or refresh:
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'env-session': self.session_mgr.get_session(role, prompt=False)}

        return self.CACHE[role]['env-session']

    def __ssm(self, role: AssumableRole, refresh: bool) -> SsmDao:
        """
        Returns an SSMDao initialized with a session for the selected ENV based on FiggyContext
        """

        if not self.CACHE.get(role, {}).get('ssm') or refresh:
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'ssm': SsmDao(self.__env_session(role, refresh).client('ssm'))}

        return self.CACHE[role]['ssm']

    def __kms(self, role: AssumableRole, refresh: bool) -> KmsSvc:
        """
        Returns a hydrated KMS Service object based on these selected ENV
        """

        if not self.CACHE.get(role, {}).get('kms') or refresh:
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'kms': KmsSvc(self.__env_session(role, refresh).client('kms'))}

        return self.CACHE[role]['kms']

    def __config(self, role: AssumableRole, refresh: bool) -> ConfigDao:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        if not self.CACHE.get(role, {}).get('dynamodb') or refresh:
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'dynamodb': ConfigDao(self.__env_session(role, refresh).resource('dynamodb'))}

        return self.CACHE[role]['dynamodb']
