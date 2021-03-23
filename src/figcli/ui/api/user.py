import logging

from abc import ABC
from typing import List

from figcli.commands.config_context import ConfigContext
from figcli.models.kms_key import KmsKey
from figcli.models.user.authed_role import AuthedRole
from figcli.models.user.user import User
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.route import Route

log = logging.getLogger(__name__)


class UserController(Controller, ABC):

    def __init__(self, prefix: str, config_context: ConfigContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, svc_registry)
        self.context: ConfigContext = config_context
        self._routes.append(Route('/user', self.get_user, ["GET"]))
        self._routes.append(Route('/authed-keys', self.get_authed_kms_keys, ["GET"]))
        self._routes.append(Route('/authed-role', self.get_authed_role, ["GET"]))
        self.user = User(name=self.context.defaults.user,
                         role=self.context.defaults.role,
                         assumable_roles=self.context.defaults.assumable_roles)

    @Controller.return_json
    def get_user(self):
        return self.user

    @Controller.return_json
    def get_authed_role(self) -> AuthedRole:
        return AuthedRole(assumable_role=self.get_role(),
                          authed_kms_keys=self._cfg_view().get_authorized_kms_keys_full(self.get_role().run_env),
                          authed_namespaces=self._cfg_view().get_authorized_namespaces())

    @Controller.return_json
    def get_authed_kms_keys(self) -> List[KmsKey]:
        return self._cfg_view().get_authorized_kms_keys_full()
