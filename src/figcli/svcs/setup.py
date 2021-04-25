import json
import logging
import os

from typing import Callable, List, Dict, Optional

from tabulate import tabulate

from figcli.commands.figgy_context import FiggyContext
from figcli.config import *
from figgy.data.dao.ssm import SsmDao
from figcli.io.input import Input
from figcli.models.assumable_role import AssumableRole
from figcli.models.defaults.defaults import CLIDefaults
from figcli.models.defaults.provider import Provider
from figcli.models.defaults.provider_config import ProviderConfigFactory
from figcli.models.role import Role
from figgy.models.run_env import RunEnv
from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.config_manager import ConfigManager
from figcli.svcs.auth.provider.provider_factory import SessionProviderFactory
from figcli.svcs.auth.provider.session_provider import SessionProvider
from figcli.svcs.auth.provider.sso_session_provider import SSOSessionProvider
from figcli.svcs.auth.session_manager import SessionManager
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.utils.secrets_manager import SecretsManager
from figcli.utils.utils import Utils
from json import JSONDecodeError

log = logging.getLogger(__name__)


class FiggySetup:
    """
    Contains logic around setting up Figgy. Configuring user auth, etc.
    """

    # If we ever need to add params to this constructor we'll need to better handle dependencies and do a bit of
    # refactoring here.
    def __init__(self, context: FiggyContext):
        self._cache_mgr = CacheManager(file_override=DEFAULTS_FILE_CACHE_PATH)
        self._config_mgr, self.c = ConfigManager.figgy(), Utils.default_colors()
        self._session_mgr = None
        self._session_provider = None
        self._secrets_mgr = SecretsManager()
        self._figgy_context = context

    def get_assumable_roles(self, defaults: CLIDefaults = None) -> List[AssumableRole]:
        if not defaults:
            defaults = self.get_defaults()

        return self._get_session_provider(defaults).get_assumable_roles()

    def _get_session_manager(self, defaults: CLIDefaults) -> SessionManager:
        if not self._session_mgr:
            self._session_mgr = SessionManager(defaults, self._get_session_provider(defaults))

        return self._session_mgr

    def _get_session_provider(self, defaults: CLIDefaults):
        if not self._session_provider:
            self._session_provider = SessionProviderFactory(defaults, self._figgy_context).instance()

        return self._session_provider

    def configure_auth(self, current_defaults: CLIDefaults, configure_provider=True) -> CLIDefaults:
        updated_defaults = current_defaults
        if configure_provider or current_defaults.provider is Provider.UNSELECTED:
            provider: Provider = Input.select_provider()
            updated_defaults.provider = provider
        else:
            provider: Provider = current_defaults.provider

        if provider in Provider.sso_providers():
            user: str = Input.get_user(provider=provider.name)
            password: str = Input.get_password(provider=provider.name)
            self._secrets_mgr.set_password(user, password)
            updated_defaults.user = user

        try:
            mfa_enabled = Utils.parse_bool(self._config_mgr.get_or_prompt(Config.Section.Figgy.MFA_ENABLED,
                                                                          Input.select_mfa_enabled, desc=MFA_DESC))
            if mfa_enabled:
                auto_mfa = Utils.parse_bool(self._config_mgr.get_or_prompt(Config.Section.Figgy.AUTO_MFA,
                                                                           Input.select_auto_mfa, desc=AUTO_MFA_DESC))
            else:
                auto_mfa = False

        except ValueError as e:
            Utils.stc_error_exit(f"Invalid value found in figgy defaults file under "
                                 f"{Config.Section.Figgy.MFA_ENABLED.value}. It must be either 'true' or 'false'")
        else:
            updated_defaults.mfa_enabled = mfa_enabled
            updated_defaults.auto_mfa = auto_mfa

        if updated_defaults.auto_mfa:
            mfa_secret = Input.get_mfa_secret()
            self._secrets_mgr.set_mfa_secret(updated_defaults.user, mfa_secret)

        if configure_provider:
            provider_config = ProviderConfigFactory().instance(provider, mfa_enabled=updated_defaults.mfa_enabled)
            updated_defaults.provider_config = provider_config

        return updated_defaults

    def configure_roles(self, current_defaults: CLIDefaults, run_env: RunEnv = None, role: Role = None) -> CLIDefaults:
        updated_defaults = current_defaults
        provider_factory: SessionProviderFactory = SessionProviderFactory(current_defaults, self._figgy_context)
        session_provider: SSOSessionProvider = provider_factory.instance()
        session_provider.cleanup_session_cache()

        # Get assertion and parse out account -> role -> run_env mappings.
        assumable_roles: List[AssumableRole] = session_provider.get_assumable_roles()
        print(f"\n{self.c.fg_bl}The following assumable roles were detected for user: {current_defaults.user} "
              f"- if something is missing, contact your system administrator.{self.c.rs}\n\n")

        if assumable_roles:
            self.print_role_table(assumable_roles)

        valid_envs = list(set([x.run_env.env for x in assumable_roles]))
        valid_roles = list(set([x.role.role for x in assumable_roles]))

        if not role:
            role: Role = Input.select_role(valid_roles=valid_roles)
            print("\n")

        if not run_env:
            run_env: RunEnv = Input.select_default_account(valid_envs=valid_envs)
            print("\n")
        else:
            print(f"\nYour default environment has been set to: {run_env}. Commands without the "
                  f"--{env.name} option will run against this account.")

        updated_defaults.run_env = run_env
        updated_defaults.valid_envs = valid_envs
        updated_defaults.valid_roles = valid_roles
        updated_defaults.assumable_roles = assumable_roles
        updated_defaults.role = role

        return updated_defaults

    def configure_preferences(self, current_defaults: CLIDefaults):
        updated_defaults = current_defaults
        updated_defaults.region = self._config_mgr.get_or_prompt(Config.Section.Figgy.AWS_REGION, Input.select_region)
        updated_defaults.colors_enabled = self._config_mgr.get_or_prompt(Config.Section.Figgy.COLORS_ENABLED,
                                                                         Input.select_enable_colors, force_prompt=True)

        # Defaulting to True, users will always be prompted to report or not report an error.
        updated_defaults.report_errors = True

        # Defaulting usage tracking to on, unless the user updates ~/.figgy/config to disable it.
        updated_defaults.usage_tracking = self._config_mgr.get_property(Config.Section.Figgy.USAGE_TRACKING,
                                                                        default=True)

        return updated_defaults

    def configure_extras(self, current_defaults: CLIDefaults):
        updated_defaults = current_defaults
        if os.environ.get(FIGGY_DISABLE_KEYRING) == 'true':
            updated_defaults.extras[DISABLE_KEYRING] = True

        return updated_defaults

    def configure_figgy_defaults(self, current_defaults: CLIDefaults):
        updated_defaults = current_defaults
        env = GlobalEnvironment(role=current_defaults.assumable_roles[0], region=current_defaults.region)
        session = self._get_session_manager(current_defaults).get_session(env,
                                                                          prompt=True)
        ssm = SsmDao(session.client('ssm'))
        default_service_ns = ssm.get_parameter(PS_FIGGY_DEFAULT_SERVICE_NS_PATH)
        updated_defaults.service_ns = default_service_ns
        updated_defaults.enabled_regions = json.loads(ssm.get_parameter(PS_FIGGY_REGIONS))

        return updated_defaults

    def basic_configure(self, configure_provider=True) -> CLIDefaults:
        defaults: CLIDefaults = self.get_defaults()
        if not defaults:
            Utils.stc_error_exit(f"Please run {CLI_NAME} --{configure.name} to set up Figgy, "
                                 f"you've got problems friend!")
        else:
            defaults = self.configure_auth(defaults, configure_provider=configure_provider)

        return defaults

    def save_defaults(self, defaults: CLIDefaults):
        self._cache_mgr.write(DEFAULTS_KEY, defaults)

    def get_defaults(self) -> CLIDefaults:
        try:
            last_write, defaults = self._cache_mgr.get(DEFAULTS_KEY)
        except Exception as e:
            # If cache is corrupted or inaccessible, "fogetaboutit" (in italian accent)
            return CLIDefaults.unconfigured()

        return defaults if defaults else CLIDefaults.unconfigured()

    @staticmethod
    def stc_get_defaults(skip: bool = False, profile: str = None) -> Optional[CLIDefaults]:
        """Lookup a user's defaults as configured by --configure option.
        :param skip - Boolean, if this is true, exit and return none.
        :param profile - AWS CLI profile to use as an override. If this is passed in all other options are ignored.
        :return: hydrated CLIDefaults object of default values stored in cache file or None if no cache found
        """
        if profile:
            return CLIDefaults.from_profile(profile)

        cache_mgr = CacheManager(file_override=DEFAULTS_FILE_CACHE_PATH)
        try:
            last_write, defaults = cache_mgr.get(DEFAULTS_KEY)
            if not defaults:
                if skip:
                    return CLIDefaults.unconfigured()
                else:
                    Utils.stc_error_exit(f'{CLI_NAME} has not been configured.\n\nIf your organization has already '
                                         f'installed Figgy Cloud, please run '
                                         f'`{CLI_NAME} --{configure.name}`.\n\n'
                                         f'You may also provide the `--profile` flag, or log-in to our free sandbox with '
                                         f'`figgy login sandbox` to experiment with {CLI_NAME}.')

            return defaults
        except JSONDecodeError:
            return None

    @staticmethod
    def print_role_table(roles: List[AssumableRole]):
        printable_roles: Dict[int: Dict] = {}
        for role in roles:
            item = printable_roles.get(role.account_id, {})
            item['env'] = role.run_env.env
            item['roles'] = item.get('roles', []) + [role.role.role]
            printable_roles[role.account_id] = item

        print(tabulate(
            [
                [
                    f'{account_id[0:5]} [REDACTED]',
                    printable_roles[account_id]['env'],
                    ', '.join(printable_roles[account_id]['roles'])
                ]
                for account_id in printable_roles.keys()
            ],
            headers=['Account #', 'Environment', 'Role'],
            tablefmt="grid",
            numalign="center",
            stralign="left",
        ))
