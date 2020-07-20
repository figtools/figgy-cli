import sys
from figcli.commands.help_context import HelpContext
from figcli.commands.types.help import HelpCommand
from figcli.config import *
from figcli.io.input import Input
from figcli.io.output import Output
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
        self._out = Output(colors_enabled=help_context.defaults.colors_enabled)

    def upgrade(self):
        latest_version: FiggyVersionDetails = self.tracker.get_version()
        install_success, upgrade_it = False, True

        if self.upgrade_mgr.is_pip_install():
            self._out.error(f"Figgy appears to have been installed with pip. Please upgrade [[{CLI_NAME}]] with "
                            f"`pip` instead.")
            self._out.print(f"\n\n[[Try this command]]: pip install figgy-cli --upgrade")

            self._out.print(f"\n\nPip based [[{CLI_NAME}]] installations do not support automatic upgrades and "
                            f"instead require pip-managed upgrades; however,  Homebrew, one-line, and manual "
                            f"installations support auto-upgrade. Please consider installing figgy through one "
                            f"of these other methods to take advantage of this feature. "
                            f"It will save you time, help keep you up-to-date, and enable important features like "
                            f"release-rollbacks and canary releases! "
                            f"[[https://www.figgy.dev/docs/getting-started/install/]]")
            sys.exit(0)

        install_path = self.upgrade_mgr.install_path

        if not install_path:
            self._utils.error_exit(f"Unable to detect local figgy installation. Please reinstall figgy and follow one "
                                   f"of the recommended installation procedures.")

        if latest_version.version == VERSION:
            self._out.success(f'You are currently using the latest version of [[{CLI_NAME}]]: [[{VERSION}]]')
            upgrade_it = False

        elif self.tracker.upgrade_available(VERSION, latest_version.version):
            self._out.notify_h2(f"New version: [[{latest_version.version}]] is more recent than your version: [[{VERSION}]]")
        else:
            self._out.notify_h2(f"Your version: [[{VERSION}]] is more recent then the current recommended version "
                                f"of {CLI_NAME}: [[{latest_version.version}]]")
            upgrade_it = Input.y_n_input(f'Would you like to revert to the current recommended version '
                                         f'of {CLI_NAME}?')

        if upgrade_it:
            if self._utils.is_mac():
                self._out.print(f"\nMacOS auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_mac(latest_version)
            elif self._utils.is_linux():
                self._out.print(f"\nLinux auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_linux(latest_version)
            elif self._utils.is_windows():
                self._out.print(f"\nWindows auto-upgrade is supported. Performing auto-upgrade.")
                install_success = self.install_windows(latest_version)

            if install_success:
                self._out.success(f"Installation successful! Exiting. Rerun `[[{CLI_NAME}]]` "
                      f"to use the latest version!")
            else:
                self._out.warn(f"\nUpgrade may not have been successful. Check by re-running "
                      f"[[`{CLI_NAME}` --version]] to see if it was. If it wasn't, please reinstall [[`{CLI_NAME}`]]. "
                      f"See {INSTALL_URL}.")

    def install_mac(self, latest_version: FiggyVersionDetails) -> bool:
        install_path = '/usr/local/bin/figgy'

        if self.upgrade_mgr.is_brew_install():
            self._out.notify_h2(f"Homebrew installation detected!")

            print(f"This upgrade process will not remove your brew installation but will instead unlink it. "
                  f"Going forward you will no longer need homebrew to manage {CLI_NAME}. Continuing is recommended.\n")

            selection = Input.y_n_input(f"Continue? ", default_yes=True)
        else:
            selection = True

        if selection:
            self.upgrade_mgr.install_onedir(install_path, latest_version.version, MAC)
            return True
        else:
            self._out.print(f'\n[[Auto-upgrade aborted. To upgrade through brew run:]] \n'
                  f'-> brew upgrade figtools/figgy/figgy')
            self._out.warn(f"\n\nYou may continue to manage [[{CLI_NAME}]] through Homebrew, but doing so will "
                           f"limit some upcoming functionality around canary releases, rollbacks, and dynamic "
                           f"version-swapping.")
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
