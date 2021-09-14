import os

import requests
from abc import ABC
import re
from typing import List

from figcli.commands.figgy_context import FiggyContext
from figcli.commands.help_context import HelpContext
from figcli.commands.types.help import HelpCommand
from figcli.config import *
from figcli.io.input import Input
from figcli.io.output import Output
from figcli.models.assumable_role import AssumableRole
from figcli.models.defaults.defaults import CLIDefaults
from figcli.models.defaults.provider import Provider
from figcli.models.role import Role
from figgy.models.run_env import RunEnv
import figcli.config.commands as commands
from figcli.svcs.aws_cfg import AWSConfig
from figcli.svcs.config_manager import ConfigManager
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.svcs.setup import FiggySetup
from figcli.svcs.auth.provider.provider_factory import SessionProviderFactory
from figcli.models.sandbox.login_response import SandboxLoginResponse
from figcli.utils.environment_validator import EnvironmentValidator
from figcli.utils.utils import Utils


class Login(HelpCommand, ABC):
    """
    Log the user into every possible environment they have access to. Sessions are cached.
    This improves figgy performance throughout the day.
    """

    def __init__(self, help_context: HelpContext, figgy_setup: FiggySetup, figgy_context: FiggyContext):
        super().__init__(login, Utils.not_windows(), help_context)
        self._setup = figgy_setup
        self._defaults: CLIDefaults = figgy_setup.get_defaults()
        self._figgy_context = figgy_context
        self._utils = Utils(self._defaults.colors_enabled)
        self._aws_cfg = AWSConfig(color=self.c)
        self._out = Output(self._defaults.colors_enabled)

        self.example = f"\n\n{self.c.fg_bl}{CLI_NAME} {login.name} \n" \
                       f"{self.c.rs}{self.c.fg_yl}  --or--{self.c.rs}\n" \
                       f"{self.c.fg_bl}{CLI_NAME} {login.name} {sandbox.name}{self.c.rs}"

    def login(self):
        self._utils.validate(self._defaults.provider.name in Provider.names(),
                             f"You cannot login until you've configured Figgy. Please run `{CLI_NAME}` --configure")
        provider = SessionProviderFactory(self._defaults, self._figgy_context).instance()
        assumable_roles: List[AssumableRole] = provider.get_assumable_roles()
        self._out.print(f"{self.c.fg_bl}Found {len(assumable_roles)} possible logins. Logging in...{self.c.rs}")

        for role in assumable_roles:
            self._out.print(f"Login successful for {role.role} in environment: {role.run_env}")
            provider.get_session_and_role(role, False)

        self._out.print(f"{self.c.fg_gr}Login successful. All sessions are cached.{self.c.rs}")

    def login_sandbox(self):
        """
        If user provides --role flag, skip role & env selection for a smoother user experience.
        """
        EnvironmentValidator(self._defaults).validate_environment_variables()

        Utils.wipe_vaults() or Utils.wipe_defaults() or Utils.wipe_config_cache()

        self._out.print(f"{self.c.fg_bl}Logging you into the Figgy Sandbox environment.{self.c.rs}")
        user = Input.input("Please input a user name: ", min_length=2)
        colors = Input.select_enable_colors()

        # Prompt user for role if --role not provided
        if commands.role not in self.context.options:
            role = Input.select("\n\nPlease select a role to impersonate: ", valid_options=SANDBOX_ROLES)
        else:
            role = self.context.role.role
            self._utils.validate(role in SANDBOX_ROLES, f"Provided role: >>>`{role}`<<< is not a valid sandbox role."
                                                        f" Please choose from {SANDBOX_ROLES}")

        params = {'role': role, 'user': user}
        result = requests.get(GET_SANDBOX_CREDS_URL, params=params)

        if result.status_code != 200:
            self._utils.error_exit("Unable to get temporary credentials from the Figgy sandbox. If this problem "
                                   f"persists please notify us on our GITHUB: {FIGGY_GITHUB}")

        data = result.json()
        response = SandboxLoginResponse(**data)
        self._aws_cfg.write_credentials(access_key=response.AWS_ACCESS_KEY_ID, secret_key=response.AWS_SECRET_ACCESS_KEY,
                                        token=response.AWS_SESSION_TOKEN, region=FIGGY_SANDBOX_REGION,
                                        profile_name=FIGGY_SANDBOX_PROFILE)

        defaults = CLIDefaults.sandbox(user=user, role=role, colors=colors)
        self._setup.save_defaults(defaults)

        run_env = RunEnv(env='dev', account_id=SANDBOX_DEV_ACCOUNT_ID) if self.context.role else None

        config_mgr = ConfigManager.figgy()
        config_mgr.set(Config.Section.Bastion.PROFILE, FIGGY_SANDBOX_PROFILE)
        defaults = self._setup.configure_extras(defaults)
        defaults = self._setup.configure_roles(current_defaults=defaults, role=Role(role=role), run_env=run_env)
        defaults = self._setup.configure_figgy_defaults(defaults)
        self._setup.save_defaults(defaults)

        self._out.success(f"\nLogin successful. Your sandbox session will last for [[1 hour]].")

        self._out.print(
            f"\nIf your session expires, you may rerun `{CLI_NAME} login sandbox` to get another sandbox session. "
            f"\nAll previous figgy sessions have been disabled, you'll need to run {CLI_NAME} "
            f"--configure to leave the sandbox.")

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        if self.context.command == login:
            self.login()
        elif self.context.command == sandbox:
            Utils.wipe_vaults() or Utils.wipe_defaults()
            self.login_sandbox()
