from typing import Dict

import boto3
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


class ServiceRegistry:
    CACHE: Dict = {}

    def __init__(self, session_mgr: SessionManager, context: CommandContext):
        self.session_mgr = session_mgr
        self.context = context
        self.__env_lock = Lock()
        self.__mgr_lock = Lock()
        self._cache_mgr = CacheManager(self.context.resource)

    def config_svc(self, role: AssumableRole):
        if not self.CACHE.get(role, {}).get('config-svc'):
            self.CACHE[role]['config-svc'] = ConfigService(self.__config(role), self.__ssm(role),
                                                           self._cache_mgr, role.run_env)

        return self.CACHE[role]['config-svc']

    def rbac_view(self, role: AssumableRole) -> RBACLimitedConfigView:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        if not self.CACHE.get(role, {}).get('rbac-view'):
            self.CACHE[role] = self.CACHE.get(role, {}) | \
                               {'rbac-view': RBACLimitedConfigView(role=role.role,
                                                                   cache_mgr=self._cache_mgr,
                                                                   ssm=self.__ssm(role),
                                                                   config_svc=self.config_svc(role),
                                                                   profile=role.profile)}

        return self.CACHE[role]['rbac-view']

    def __env_session(self, role: AssumableRole) -> boto3.session.Session:
        """
        Lazy load an ENV session object for the ENV selected in the FiggyContext
        :return: Hydrated session for the selected environment.
        """
        if not self.CACHE.get(role, {}).get('env-session'):
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'env-session': self.session_mgr.get_session(role, prompt=False)}

        return self.CACHE[role]['env-session']

    def __ssm(self, role: AssumableRole) -> SsmDao:
        """
        Returns an SSMDao initialized with a session for the selected ENV based on FiggyContext
        """

        if not self.CACHE.get(role, {}).get('ssm'):
            self.CACHE[role] = self.CACHE.get(role, {}) | {'ssm': SsmDao(self.__env_session(role).client('ssm'))}

        return self.CACHE[role]['ssm']

    def __kms(self, role: AssumableRole) -> KmsSvc:
        """
        Returns a hydrated KMS Service object based on these selected ENV
        """

        if not self.CACHE.get(role, {}).get('kms'):
            self.CACHE[role] = self.CACHE.get(role, {}) | {'kms': KmsSvc(self.__env_session(role).client('kms'))}

        return self.CACHE[role]['kms']

    def __config(self, role: AssumableRole) -> ConfigDao:
        """
        Returns a hydrated ConfigDao for the selected environment.
        """
        if not self.CACHE.get(role, {}).get('dynamodb'):
            self.CACHE[role] = self.CACHE.get(role, {}) | {
                'dynamodb': ConfigDao(self.__env_session(role).resource('dynamodb'))}

        return self.CACHE[role]['dynamodb']
