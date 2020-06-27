import sys
from figcli.commands.help_context import HelpContext
from figcli.commands.types.help import HelpCommand
from figcli.config import *
from figcli.input import Input
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker, FiggyVersionDetails
from figcli.svcs.upgrade_manager import UpgradeManager
from figcli.utils.utils import Utils


class Upgrade(HelpCommand):
    """
    Drives the --version command
    """

    def __init__(self, help_context: HelpContext):
        super().__init__(version, help_context.defaults.colors_enabled, help_context)
        self.tracker = VersionTracker(self.context.defaults)
        self.upgrade_mgr = UpgradeManager(help_context.defaults.colors_enabled)
        self._utils = Utils(colors_enabled=help_context.defaults.colors_enabled)

    def upgrade(self):
        latest_version: FiggyVersionDetails = self.tracker.get_version()
        install_success, upgrade_it = False, True

        if self.upgrade_mgr.is_pip_install():
            print(f"{self.c.fg_rd}Figgy appears to have been installed with pip. Please upgrade {CLI_NAME} with "
                  f"`pip` instead.{self.c.rs}")
            print(f"\n\n{self.c.fg_bl}Try this command:{self.c.rs} pip install figgy-cli --upgrade")

            print(f"\n\n{self.c.fg_bl}Figgy supports automatic figgy-managed upgrades. Homebrew and manual "
                  f"installations support this feature. Python pip installations require pip-managed upgrades. "
                  f"Please consider installing figgy through one of these methods to take advantage of this feature. "
                  f"It will save you time, help keep you up-to-date, and enable important features like "
                  f"release-rollbacks and canary releases! https://www.figgy.dev/docs/getting-started/install/")
            sys.exit(0)

        install_path = self.upgrade_mgr.install_path

        if not install_path:
            self._utils.error_exit(f"Unable to detect local figgy installation. Please reinstall figgy and follow one "
                                   f"of the recommended installation procedures.")

        if latest_version.version == VERSION:
            print(f'{self.c.fg_bl}You are currently using the latest version of {CLI_NAME}: {self.c.rs}'
                  f'{self.c.fg_gr}{VERSION}{self.c.rs}')

        elif self.tracker.upgrade_available(VERSION, latest_version.version):
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')
            print(f' New version: {self.c.rs}{self.c.fg_gr}{latest_version.version}{self.c.rs} is more '
                  f'recent than your version: {self.c.fg_gr}{VERSION}{self.c.rs}')
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')

        else:
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')
            print(f'Your version: {self.c.rs}{self.c.fg_gr}{VERSION}{self.c.rs} is more '
                  f'recent than the current recommended version of {CLI_NAME}: {self.c.fg_gr}'
                  f'{latest_version.version}{self.c.rs}')
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')

            upgrade_it = Input.y_n_input(f'Would you like to revert to the current recommended version '
                                         f'of {CLI_NAME}?')

        if upgrade_it:
            if self._utils.is_mac():
                print(f"\nMacOS auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_mac(latest_version)
            elif self._utils.is_linux():
                print(f"\nLinux auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_linux(latest_version)
            elif self._utils.is_windows():
                print(f"\nWindows auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_windows(latest_version)

            if install_success:
                print(f"{self.c.fg_gr}Installation successful! Exiting. Rerun `{CLI_NAME}` "
                      f"to use the latest version!{self.c.rs}")
            else:
                print(f"\n{self.c.fg_yl}Upgrade may not have been successful. Check by re-running "
                      f"`{CLI_NAME}` --version to see if it was. If it wasn't, please reinstall `{CLI_NAME}`. "
                      f"See {INSTALL_URL}.")

    def install_mac(self, latest_version: FiggyVersionDetails) -> bool:
        if self.upgrade_mgr.is_brew_install():
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')
            print(f'{self.c.fg_bl}    Homebrew installation detected! {self.c.rs}')
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')

            print(f"This upgrade process will not remove your brew installation but will instead unlink it. "
                  f"Going forward you will no longer need homebrew to manage {CLI_NAME}. Continuing is recommended.\n")

            selection = Input.y_n_input(f"Continue? ", default_yes=True)
            install_path = '/usr/local/bin/figgy'
        else:
            install_path = self.upgrade_mgr.install_path
            selection = True

        if selection:
            self.upgrade_mgr.install_onedir(install_path, latest_version.version, MAC)
            return True
        else:
            print(f'\n{self.c.fg_bl}Auto-upgrade aborted. To upgrade through brew run:{self.c.rs} \n'
                  f'-> brew upgrade figtools/figgy/figgy')
            print(f"\n\n{self.c.fg_yl}You may continue to manage {CLI_NAME} through homebrew, but doing so will limit some "
                  f" upcoming functionality around canary releases, rollbacks, and dynamic version-swapping.{self.c.rs}")
            return False

    def install_linux(self, latest_version: FiggyVersionDetails) -> bool:
        install_path = self.upgrade_mgr.install_path
        self.upgrade_mgr.install_onedir(install_path, latest_version.version, LINUX)
        return True

    def install_windows(self, latest_version: FiggyVersionDetails) -> bool:
        install_path = self.upgrade_mgr.install_path
        self.upgrade_mgr.install_onedir(install_path, latest_version.version, WINDOWS)
        return True

    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self.upgrade()
