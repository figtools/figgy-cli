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
        # self._utils.error_exit("This command has been deprecated and disabled. Please use the standard upgrade process"
        #                        "through `homebrew` or `pip`.")
        latest_version: FiggyVersionDetails = self.tracker.get_version()
        install_success = False

        if self.upgrade_mgr.is_pip_install():
            print(f"{self.c.fg_rd}Figgy appears to have been installed with pip. Please upgrade {CLI_NAME} with "
                  f"`pip` instead.{self.c.rs}")
            print(f"\n\n{self.c.fg_bl}Try this command:{self.c.rs} pip install figgy-cli --upgrade")

            print(f"\n\n{self.c.fg_bl}Figgy supports automatic figgy-managed upgrades. Installing Figgy with brew or "
                  f"via the manual installation process (still easy) supports this feature. Only pip installations "
                  f"require pip-managed upgrades.")
            sys.exit(0)

        install_path = self.upgrade_mgr.install_path

        if not install_path:
            self._utils.error_exit(f"Unable to detect local figgy installation. Please reinstall figgy and follow one "
                                   f"of the recommended installation procedures.")

        print(f"\n{self.c.fg_bl}Detected local installation path:{self.c.rs} {install_path}")

        if latest_version.version == VERSION:
            print(f'{self.c.fg_bl}You are currently using the latest version of {CLI_NAME}: {self.c.rs}'
                  f'{self.c.fg_gr}{VERSION}{self.c.rs}')

        elif self.tracker.upgrade_available(VERSION, latest_version.version):
            print(f'{self.c.fg_yl}--------------------------------------------------------------{self.c.rs}')
            print(f' New version: {self.c.rs}{self.c.fg_gr}{latest_version.version}{self.c.rs} is more '
                  f'recent than your version: {self.c.fg_gr}{VERSION}{self.c.rs}')
            print(f'{self.c.fg_yl}--------------------------------------------------------------{self.c.rs}')

            if self._utils.is_mac():
                print(f"\nMacOS auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_mac(latest_version)
            elif self._utils.is_linux():
                print(f"\nLinux auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_linux(latest_version)

            if install_success:
                print(f"{self.c.fg_gr}Installation successful! Exiting. Rerun `{CLI_NAME}` "
                      f"to use the latest version!{self.c.rs}")
        else:
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')
            print(f'Your version: {self.c.rs}{self.c.fg_gr}{latest_version.version}{self.c.rs} is more '
                  f'recent than the current recommended version of {CLI_NAME}: {self.c.fg_gr}{VERSION}{self.c.rs}')
            print(f'{self.c.fg_yl}------------------------------------------{self.c.rs}')

            if self._utils.is_mac():
                selection = Input.y_n_input(f'Would you like to revert to the current recommended version '
                                            f'of {CLI_NAME}?')
                if selection:
                    self.install_mac(latest_version)

    def install_mac(self, latest_version: FiggyVersionDetails):
        selection = Input.y_n_input(f"Have {CLI_NAME} auto-update? Figgy will overwrite any homebrew-created {CLI_NAME} "
                                    f"symlink. Going forward you will no longer need homebrew to manage Figgy. "
                                    f"Continue (recommended)? ", default_yes=True)
        if selection:
            install_path = self.upgrade_mgr.install_path
            self.upgrade_mgr.install_onedir(install_path, latest_version.version, MAC)
        else:
            print(f'\n{self.c.fg_bl}Auto-upgrade aborted. To upgrade through brew:{self.c.rs} '
                  f'brew upgrade figtools/figgy/figgy')
            print(f"\n\n{self.c.fg_yl}You may continue to manage {CLI_NAME} through homebrew. Doing so will limit some "
                  f" upcoming functionality around release rollbacks and dynamic version-swapping. ")

    def install_linux(self, latest_version: FiggyVersionDetails):
        install_path = self.upgrade_mgr.install_path
        self.upgrade_mgr.install_onedir(install_path, latest_version.version, LINUX)

    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self.upgrade()
