import json
import logging
from abc import ABC
from typing import List

from flask import request

from figcli.commands.command_context import CommandContext
from figcli.models.assumable_role import AssumableRole
from figcli.models.kms_key import KmsKey
from figcli.models.user.authed_role import AuthedRole
from figcli.models.user.user import User
from figcli.svcs.service_registry import ServiceRegistry
from figcli.ui.controller import Controller
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.ui.route import Route

log = logging.getLogger(__name__)


class UserController(Controller, ABC):

    def __init__(self, prefix: str, context: CommandContext, svc_registry: ServiceRegistry):
        super().__init__(prefix, context, svc_registry)
        self._routes.append(Route('/user', self.get_user, ["GET"]))
        self._routes.append(Route('/authed-keys', self.get_authed_kms_keys, ["GET"]))
        self._routes.append(Route('/authed-role', self.get_authed_role, ["GET"]))
        self._routes.append(Route('/reauth', self.reauthenticate, ["POST"]))
        self._routes.append(Route('/regions', self.get_enabled_regions, ["GET"]))
        self.user = User(name=self.context.defaults.user,
                         role=self.context.defaults.role,
                         assumable_roles=self.context.defaults.assumable_roles,
                         enabled_regions=self.context.defaults.enabled_regions
                                         or [self.context.defaults.region])

    @Controller.return_json
    def get_user(self):
        return self.user

    @Controller.return_json
    def get_authed_role(self):
        role = AuthedRole(assumable_role=self.get_environment().role,
                          authed_kms_keys=self._cfg_view().get_authorized_kms_keys_full(
                              self.get_environment().role.run_env),
                          authed_namespaces=self._cfg_view().get_authorized_namespaces())

        return role

    @Controller.return_json
    def get_authed_kms_keys(self) -> List[KmsKey]:
        return self._cfg_view().get_authorized_kms_keys_full()

    @Controller.build_response
    def reauthenticate(self):
        mfa = request.args.get('mfa', None)
        envs: List[GlobalEnvironment] = []
        for role in self.user.assumable_roles:
            for region in self.user.enabled_regions:
                envs.append(GlobalEnvironment(role=role, region=region))

        return self._registry.auth_roles(envs, mfa=mfa)


    @Controller.build_response
    def get_enabled_regions(self, refresh: bool = False):
        """
        This call occurs during app INIT and cannot require the "region" header as we can't possibly know what
        region before we've requested the enabled regions.
        """
        log.info(f'Active role: {request.headers.get("ActiveRole")} and region {self.context.defaults.region}')
        env: GlobalEnvironment = GlobalEnvironment(role=AssumableRole(**json.loads(request.headers.get('ActiveRole'))),
                                                   region=self.context.defaults.region)

        return {'regions': self._cfg(refresh, env).get_all_regions()}
