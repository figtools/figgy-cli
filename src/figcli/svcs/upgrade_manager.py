import os
import readline
import stat
import sys
import logging
from typing import Optional
from urllib.request import urlopen

import requests
from zipfile import ZipFile

from tqdm import tqdm
from figcli.extras.completer import Completer

from figcli.config import HOME, CLI_NAME
from figcli.svcs.observability.version_tracker import FiggyVersionDetails, VersionTracker
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)

class UpgradeManager:
    def __init__(self, colors_enabled: bool):
        self._utils = Utils(colors_enabled=colors_enabled)
        self.c = Utils.default_colors(enabled=colors_enabled)
        self.current_version: FiggyVersionDetails = VersionTracker.get_version()

    def download(self, remote_path: str, local_path: str):
        eg_link = remote_path
        response = requests.get(eg_link, stream=True)
        with tqdm.wrapattr(open(local_path, "wb"), "write",
                           miniters=1, desc=eg_link.split('/')[-1],
                           total=int(response.headers.get('content-length', 0))) as fout:
            for chunk in response.iter_content(chunk_size=4096):
                fout.write(chunk)

    def is_symlink(self, install_path: str):
        return os.path.islink(install_path)

    def is_pip_install(self) -> bool:
        install_path = self.install_path
        try:
            if install_path:
                with open(install_path, 'r') as file:
                    contents = file.read()

                return 'EASY-INSTALL' in contents or 'console_scripts' in contents
            else:
                return False
        except UnicodeDecodeError as e:
            log.info(f"Error decoding {install_path}, file must be binary.")
            return False

    def install_onedir(self, install_path: str, latest_version: str, platform: str):
        zip_path = f"{HOME}/.figgy/figgy.zip"
        install_dir = f'{HOME}/.figgy/installations/{latest_version}'
        remote_path = f'http://www.figgy.dev/releases/cli/{latest_version}/{platform.lower()}/figgy.zip'
        os.makedirs(os.path.dirname(install_dir), exist_ok=True)
        suffix = ".exe" if Utils.is_windows() else ""
        self.download(remote_path, zip_path)

        with ZipFile(zip_path, 'r') as zipObj:
            zipObj.extractall(install_dir)

        if self._utils.file_exists(install_path):
            os.remove(install_path)

        executable_path = f'{install_dir}/{CLI_NAME}{suffix}'
        st = os.stat(executable_path)
        os.chmod(executable_path, st.st_mode | stat.S_IEXEC)
        os.symlink(f'{install_dir}/{CLI_NAME}', install_path)
        print(f'{CLI_NAME} has been installed at path `{install_path}`.')

    def _get_executable_path(self):
        return

    @property
    def install_path(self) -> Optional[str]:
        """
        Prompts the user to get their local installation path.
        """
        readline.parse_and_bind("tab: complete")
        comp = Completer()
        readline.set_completer_delims(' \t\n')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(comp.pathCompleter)
        abs_path = os.path.dirname(sys.executable)
        suffix = ".exe" if self._utils.is_windows() else ""
        binary_path = f'{abs_path}/{CLI_NAME}{suffix}'

        if not os.path.exists(binary_path):
            return None

        # install_path = input(f'Input path to your existing installation. Default: {abs_path} : ') or abs_path
        #

        #
        #     install_path = f"{install_path}/{CLI_NAME}{suffix}"
        #
        # if not self._utils.file_exists(install_path):
        #     self._utils.error_exit("Invalid install path specified, try providing the full path to the binary.")

        return binary_path