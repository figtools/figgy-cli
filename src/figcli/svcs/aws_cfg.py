import logging
import os

from figcli.config.style.color import Color
from figcli.io.input import Input
from figcli.svcs.config_manager import ConfigManager
from figcli.config.aws import *
from figcli.config.constants import *

log = logging.getLogger(__name__)


class AWSConfig:
    """
    Utility methods for interacting with AWSCLI resources, such as the ~/.aws/credentials and ~/.aws/config files
    """

    def __init__(self, color: Color = Color(False)):
        self.init_files()
        self.c = color
        self._config = ConfigManager(AWS_CONFIG_FILE_PATH)
        self._creds = ConfigManager(AWS_CREDENTIALS_FILE_PATH)

    @staticmethod
    def init_files():
        os.makedirs(os.path.dirname(AWS_CREDENTIALS_FILE_PATH), exist_ok=True)

        if not os.path.exists(AWS_CREDENTIALS_FILE_PATH):
            with open(AWS_CREDENTIALS_FILE_PATH, "w+") as file:
                file.write("")

        if not os.path.exists(AWS_CONFIG_FILE_PATH):
            with open(AWS_CONFIG_FILE_PATH, "w+") as file:
                file.write("")

    def _is_temporary_session(self, profile_name: str):
        if self._creds.has_section(profile_name):
            return self._creds.has_option(profile_name, AWS_CFG_TOKEN)
        return False

    def _backup_section(self, section: str):
        backup_name, backup_profile = f'{section}-figgy-backup', f'profile {section}-figgy-backup'
        profile_name = f'profile {section}'
        if self._creds.has_section(section):
            for opt in self._creds.options(section):
                self._creds.set_config(backup_name, opt, self._creds.get_option(section, opt))

        if self._config.has_section(profile_name):
            for opt in self._config.options(profile_name):
                self._config.set_config(backup_profile, opt, self._config.get_option(profile_name, opt))

    def restore(self, profile_name: str) :
        """
        Restore a credentials previously backed up by Figgy
        """
        config_profile = f'profile {profile_name}'
        backup_name, backup_profile = f'{profile_name}-figgy-backup', f'profile {profile_name}-figgy-backup'
        creds_restored, config_restored = False, False
        if self._creds.has_section(backup_name):
            for opt in self._creds.options(backup_name):
                self._creds.set_config(profile_name, opt, self._creds.get_option(backup_name, opt))
                creds_restored = True

        if self._config.has_section(backup_profile):
            for opt in self._config.options(backup_profile):
                self._config.set_config(config_profile, opt, self._config.get_option(backup_profile, opt))
                config_restored = True

        self._creds.delete(profile_name, AWS_CFG_TOKEN)
        self._creds.save()
        self._config.save()

        if creds_restored and config_restored:
            print(f"\n{self.c.fg_gr}Restoration successful!{self.c.rs}")
        else:
            print(f"\n{self.c.fg_yl}Unable to restore credentials. Profile: "
                  f"{self.c.fg_bl}[{backup_name}]{self.c.rs}{self.c.fg_yl} was not found in either the "
                  f"~/.aws/credentials or ~/.aws/config files.{self.c.rs}")

    def write_credentials(self, access_key: str, secret_key: str, token: str, region: str,
                          profile_name: str = 'default') -> None:
        """
        Overwrite credentials stored in the [default] profile in both ~/.aws/config and ~/.aws/credentials file
        with the provided temporary credentials. This method also CREATES these files if they do not already exist.
        """

        if not self._is_temporary_session(profile_name):
            print(f"\n{self.c.fg_yl}Existing AWS Profile {self.c.fg_bl}[{profile_name}]{self.c.rs}{self.c.fg_yl} "
                  f"was found with long-lived access keys "
                  f"in file: {self.c.fg_bl}~/.aws/credentials{self.c.rs}{self.c.fg_yl}.\n"
                  f"To avoid overwriting these keys, they will be moved under profile: "
                  f"{self.c.rs}{self.c.fg_bl}[{profile_name}-figgy-backup]{self.c.rs}{self.c.fg_yl}.{self.c.rs}\n\n"
                  f"These old keys may be restored with: {self.c.fg_bl}`"
                  f"{CLI_NAME} iam restore`{self.c.rs}.")
            self._backup_section(profile_name)

        self._creds.set_config(profile_name, AWS_CFG_ACCESS_KEY_ID, access_key)
        self._creds.set_config(profile_name, AWS_CFG_SECRET_KEY, secret_key)
        self._creds.set_config(profile_name, AWS_CFG_TOKEN, token)

        config_section = f'profile {profile_name}'
        self._config.set_config(config_section, AWS_CFG_REGION, region)
        self._config.set_config(config_section, AWS_CFG_OUTPUT, 'json')

        print(f"\n\n{self.c.fg_gr}Successfully updated: {AWS_CREDENTIALS_FILE_PATH}{self.c.rs}")
        print(f"{self.c.fg_gr}Successfully updated: {AWS_CONFIG_FILE_PATH}{self.c.rs}")
