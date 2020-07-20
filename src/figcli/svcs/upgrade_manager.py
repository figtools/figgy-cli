import os
import readline
import stat
import sys
import time
import logging
import uuid
from typing import Optional
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

    def download(self, url: str, local_path: str):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)

    def download_with_progress(self, url: str, local_path: str):
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        with open(local_path, 'wb+') as file, tqdm(
                desc='Downloading',
                total=total,
                unit='iB',
                miniters=1,
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

        return True

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

    def is_brew_install(self) -> bool:
        return "Cellar" in self.install_path

    def install_onedir(self, install_path: str, latest_version: str, platform: str):
        old_path = f'{install_path}.OLD'
        zip_path = f"{HOME}/.figgy/figgy.zip"
        install_dir = f'{HOME}/.figgy/installations/{latest_version}/{str(uuid.uuid4())[:4]}'
        url = f'http://www.figgy.dev/releases/cli/{latest_version}/{platform.lower()}/figgy.zip'
        os.makedirs(os.path.dirname(install_dir), exist_ok=True)
        suffix = ".exe" if Utils.is_windows() else ""
        self._cleanup_file(zip_path)

        self.download_with_progress(url, zip_path)

        with ZipFile(zip_path, 'r') as zipObj:
            zipObj.extractall(install_dir)

        if self._utils.file_exists(old_path):
            os.remove(old_path)

        executable_path = f'{install_dir}/figgy/{CLI_NAME}{suffix}'
        st = os.stat(executable_path)
        os.chmod(executable_path, st.st_mode | stat.S_IEXEC)

        if self._utils.file_exists(install_path):
            os.rename(install_path, old_path)

        os.symlink(executable_path, install_path)

    def _get_executable_path(self):
        return

    def _cleanup_file(self, file_path: str):
        try:
            os.remove(file_path)
        except Exception as e:
            log.error(f"Received error when attempting to prune install.")
            pass

    @property
    def install_path(self) -> Optional[str]:
        """
        Prompts the user to get their local installation path.
        """
        binary_path = sys.executable
        suffix = ".exe" if self._utils.is_windows() and not binary_path.endswith(".exe") else ""
        binary_path = f'{binary_path}{suffix}'

        if not os.path.exists(binary_path):
            return None

        return binary_path
