from typing import Optional, Tuple, Dict

import cachetools.func
import requests
import logging
import random
import os
import re

from pydantic import BaseModel

from figcli.config.constants import *
from figcli.config.style.color import Color
from figcli.config.style.terminal_factory import TerminalFactory
from figcli.io.output import Output
from figcli.models.defaults.defaults import CLIDefaults
from figcli.svcs.config import ConfigService

log = logging.getLogger(__name__)


class FiggyVersionDetails(BaseModel):
    version: str
    notify_chance: int
    changelog: str
    cloud_version_requirement: str

    def changes_from(self, old_version: str):
        regex = f'.*(##+\s+{self.version}.*)##+\s+{old_version}.*'
        result = re.match(regex, self.changelog, re.DOTALL)
        if result:
            return result.group(1).rstrip()
        else:
            return f"Unable to parse changes for new version: {self.version}"

    @staticmethod
    def from_api_response(response: Dict) -> "FiggyVersionDetails":
        notify_chance, version, changelog = \
            response.get('notify_chance'), response.get('version'), response.get('changelog')

        if not notify_chance or notify_chance == 'None':
            notify_chance = 0

        if not version:
            raise ValueError('No valid version found.')
        elif not changelog:
            raise ValueError('No valid changelog found.')

        return FiggyVersionDetails(
            version=version,
            notify_chance=int(notify_chance),
            changelog=response.get('changelog'),
            cloud_version_requirement=response.get('cloud_version_requirement')
        )


class VersionTracker:
    _UPGRADE_CHECK_PERCENTAGE = 5  # % chance any decorated method execution will check for an upgrade
    _DISABLE_CHECK_ENV_VAR = "FIGGY_DISABLE_VERSION_CHECK"

    def __init__(self, cli_defaults: CLIDefaults, config_service: ConfigService):
        self._cli_defaults = cli_defaults
        self.c = TerminalFactory(self._cli_defaults.colors_enabled).instance().get_colors()
        self._config = config_service
        self._out = Output(colors_enabled=cli_defaults.colors_enabled)

    @staticmethod
    @cachetools.func.ttl_cache(maxsize=2, ttl=100)
    def get_version() -> FiggyVersionDetails:
        result = requests.get(FIGGY_GET_VERSION_URL)
        if result.status_code == 200:
            details: FiggyVersionDetails = FiggyVersionDetails.from_api_response(result.json())
            return details
        else:
            raise ValueError("Unable to fetch figgy version details.")

    @staticmethod
    def check_version(c: Color) -> None:
        try:
            new_details = VersionTracker.get_version()

            if new_details.version != VERSION:
                VersionTracker.print_new_version_msg(c, new_details, print_version_text=False)
                VersionTracker.print_changes(c, new_details)
            else:
                print(f"Version: {VERSION}.")
                print(f"You are currently running the latest version of figgy.")

        except ValueError as e:
            log.warning("Unable to fetch version information from remote endpoint.")
            print(f"Version: {VERSION}")

    @staticmethod
    def print_changes(c: Color, new_details: FiggyVersionDetails) -> None:
        if new_details.version != VERSION:
            print(f'\n\n{c.fg_yl}Changes you\'ll get if you upgrade!{c.rs}')
            print(f'{c.fg_bl}------------------------------------------{c.rs}')
            print(new_details.changes_from(VERSION))
            print(f'{c.fg_bl}------------------------------------------{c.rs}')

    @staticmethod
    def print_new_version_msg(c: Color, new_details: FiggyVersionDetails, print_version_text=True):
        if not VersionTracker.is_rollback(VERSION, new_details.version):
            print(f'\n{c.fg_bl}----------------------------------------------{c.rs}')
            print(f'A new version of figgy is available!')
            print(f"Current Version: {c.fg_yl}{VERSION}{c.rs}")
            print(f"New Version: {c.fg_bl}{new_details.version}{c.rs}")
            if print_version_text:
                print(f"To see what the new version has in store for you, run `{CLI_NAME} --version`")
            print(f"To upgrade, run `{CLI_NAME} --upgrade`")
            print(f'{c.fg_bl}------------------------------------------------{c.rs}')
        else:
            print(f'\n{c.fg_bl}----------------------------------------------{c.rs}')
            print(f'Figgy was rolled back due to an issue and you\'re on a bad version!')
            print(f"Current Version: {c.fg_yl}{VERSION}{c.rs}")
            print(f"Recommended Version: {c.fg_bl}{new_details.version}{c.rs}")
            print(f"To roll-back, run `{CLI_NAME} --upgrade` (upgrade will roll-back your install)")
            print(f'{c.fg_bl}-----------------------------------------------{c.rs}')

    @staticmethod
    def is_rollback(current_version: str, new_version: str):
        try:
            cu_major = current_version.split('.')[0]
            cu_minor = current_version.split('.')[1]
            cu_patch = current_version.split('.')[2].strip('ab')
            new_major = new_version.split('.')[0]
            new_minor = new_version.split('.')[1]
            new_patch = new_version.split('.')[2].strip('ab')

            if new_major < cu_major:
                return True
            elif new_major <= cu_major and new_minor < cu_minor:
                return True
            elif new_major <= cu_major and new_minor <= cu_minor and new_patch < cu_patch:
                return True
            else:
                return False
        except IndentationError:
            pass

    def current_version(self):
        return VERSION

    @cachetools.func.ttl_cache(maxsize=2, ttl=100)
    def current_cloud_version(self):
        return self._config.get_fig_simple(PS_CLOUD_VERSION_PATH).value

    @cachetools.func.ttl_cache(maxsize=2, ttl=100)
    def required_cloud_version(self):
        details: FiggyVersionDetails = self.get_version()
        return details.cloud_version_requirement

    def cloud_version_compatible_with_upgrade(self):
        req_cloud_version = self.required_cloud_version()
        current_cloud_version: str = self.current_cloud_version()

        cl_req_major = req_cloud_version.split('.')[0]
        cl_req_minor = req_cloud_version.split('.')[1]
        cl_req_patch = req_cloud_version.split('.')[2].strip('ab')
        cl_cur_major = current_cloud_version.split('.')[0]
        cl_cur_minor = current_cloud_version.split('.')[1]
        cl_cur_patch = current_cloud_version.split('.')[2].strip('ab')

        return cl_cur_major > cl_req_major or \
               (cl_cur_major == cl_req_major and cl_cur_minor >= cl_req_minor) or \
               (cl_cur_major == cl_req_major and cl_cur_minor == cl_req_minor and cl_cur_patch >= cl_req_patch)

    def upgrade_available(self):
        try:
            current_version = VERSION
            details: FiggyVersionDetails = self.get_version()
            new_version = details.version

            cu_major = current_version.split('.')[0]
            cu_minor = current_version.split('.')[1]
            cu_patch = current_version.split('.')[2].strip('ab')
            new_major = new_version.split('.')[0]
            new_minor = new_version.split('.')[1]
            new_patch = new_version.split('.')[2].strip('ab')

            if self.cloud_version_compatible_with_upgrade():
                if new_major > cu_major:
                    return True
                elif new_major >= cu_major and new_minor > cu_minor:
                    return True
                elif new_major >= cu_major and new_minor >= cu_minor and new_patch > cu_patch:
                    return True
                else:
                    return False

            return False
        except IndentationError:
            pass

    @staticmethod
    def notify_user(function):
        """
        Has a _chance_ to notify a user if a new version has been released and they are on the old version.
        """

        log.info("Rolling dice for update notify chance")

        def inner(self, *args, **kwargs):
            if os.environ.get(VersionTracker._DISABLE_CHECK_ENV_VAR) == "true":
                return function(self, *args, **kwargs)

            log.info("Rolling dice to check version..")
            if VersionTracker._UPGRADE_CHECK_PERCENTAGE >= random.randint(1, 100):
                log.info("Checking for new version..")
                try:
                    details = VersionTracker.get_version()
                    if details.notify_chance >= random.randint(1, 100) and details.version != VERSION:
                        log.info("Notifying user of new version")
                        if hasattr(self, 'c') and isinstance(self.c, Color):
                            VersionTracker.print_new_version_msg(self.c, details)
                except ValueError:
                    log.warning("Unable to fetch version information from remote resource.")

            return function(self, *args, **kwargs)

        return inner
