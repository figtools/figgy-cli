import jsonpickle
import uuid
import os

from pydantic import BaseModel

from figcli.models.assumable_role import AssumableRole
from figcli.models.defaults.provider import Provider
from figcli.models.defaults.provider_config import ProviderConfig, ProviderConfigFactory, BastionProviderConfig
from figcli.models.role import Role
from figgy.models.run_env import RunEnv
from figcli.config import *
from typing import Dict, Optional, List, Any
from figcli.utils.utils import Utils


class CLIDefaults(BaseModel):
    """
    Defaults are parsed from the ~/.figgy/devops/defaults file and then hydrate this object
    """
    user_id: Optional[str]
    role: Optional[Role]
    colors_enabled: bool
    run_env: RunEnv
    region: str
    mfa_enabled: bool
    service_ns: str
    provider: Provider
    session_duration: int
    usage_tracking: bool
    report_errors: Optional[bool]
    auto_mfa: Optional[bool]
    provider_config: Optional[Any]
    mfa_serial: Optional[str]
    user: Optional[str]
    valid_envs: Optional[List[RunEnv]] = []
    valid_roles: Optional[List[Role]] = []
    assumable_roles: Optional[List[AssumableRole]] = []
    enabled_regions: Optional[List[str]] = []
    extras: Optional[Dict] = []

    def __str__(self):
        return f"Role: {self.role}\nColors Enabled: {self.colors_enabled}\nOkta User: {self.user}\n" \
               f"Default Environment: {self.run_env}"

    @staticmethod
    def unconfigured():
        return CLIDefaults(role=Role(role="unconfigured"),
                           colors_enabled=False,
                           user=None,
                           run_env=RunEnv(env="unconfigured"),
                           provider=Provider.UNSELECTED,
                           session_duration=DEFAULT_SESSION_DURATION,
                           region="us-east-1",
                           mfa_enabled=False,
                           mfa_serial=None,
                           provider_config=None,
                           report_errors=False,
                           auto_mfa=False,
                           user_id=str(uuid.uuid4()),
                           service_ns="/app",
                           usage_tracking=False,
                           extras={},
                           enabled_regions=["us-east-1"])

    @staticmethod
    def sandbox(user: str, role: str, colors: bool):
        return CLIDefaults(role=Role(role=role),
                           colors_enabled=colors,
                           user=user,
                           run_env=RunEnv(env="unconfigured"),
                           provider=Provider.AWS_BASTION,
                           session_duration=SANDBOX_SESSION_DURATION,
                           region=FIGGY_SANDBOX_REGION,
                           mfa_enabled=False,
                           mfa_serial=None,
                           provider_config=BastionProviderConfig(profile_name=FIGGY_SANDBOX_PROFILE),
                           report_errors=False,
                           auto_mfa=False,
                           user_id=str(uuid.uuid4()),
                           service_ns="/app",
                           usage_tracking=True,
                           extras={DISABLE_KEYRING: True},
                           enabled_regions=["us-east-1"])

    @staticmethod
    def from_profile(profile):
        return CLIDefaults(role=Role(role=profile),
                           colors_enabled=Utils.not_windows(),
                           user=profile,
                           run_env=RunEnv(env=profile),
                           provider=Provider.PROFILE,
                           session_duration=DEFAULT_SESSION_DURATION,
                           region="us-east-1",
                           mfa_enabled=False,
                           mfa_serial=None,
                           provider_config=None,
                           report_errors=False,
                           auto_mfa=False,
                           user_id=str(uuid.uuid4()),
                           service_ns=os.environ.get(APP_NS_OVERRIDE) or "/app",
                           usage_tracking=True,
                           extras={},
                           enabled_regions=["us-east-1"])
