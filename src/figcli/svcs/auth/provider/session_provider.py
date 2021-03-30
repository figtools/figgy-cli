import logging
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set, Dict

import boto3
from botocore.exceptions import ClientError
from pydantic import validator
from pydantic.decorator import BaseModel

from figcli.io.input import Input
from figcli.models.assumable_role import AssumableRole
from figcli.models.defaults.defaults import CLIDefaults
from figcli.utils.secrets_manager import SecretsManager
from figcli.utils.utils import Utils
from threading import Lock

log = logging.getLogger(__name__)


class SessionTokenCache(BaseModel):
    MAX_LIFE = 600  # 10 mins
    token: str
    time_inserted: Optional[int] = time.time()

    @validator('time_inserted', pre=True)
    def init_error(cls, value):
        log.info(f"Time was: {value}")
        value = time.time()
        log.info(f"Setting to: {value}")

        return value

    def is_valid(self):
        log.info(f"Session as inserted at {self.time_inserted} and is now {time.time() - self.time_inserted} "
                 f"seconds old. Is valid: {time.time() - self.time_inserted < self.MAX_LIFE}")
        return time.time() - self.time_inserted < self.MAX_LIFE

    def __eq__(self, o):
        return o.token == self.token

# Todo: Does multithreading fuck this up?
class SessionProvider(ABC):
    def __init__(self, defaults: CLIDefaults):
        self._defaults = defaults
        self._valid_tokens: Dict[str: SessionTokenCache] = {}
        # self._lock = Lock()
        self._secrets_mgr = SecretsManager()

    @Utils.retry
    @Utils.trace
    def _is_valid_session(self, session: boto3.Session):
        """Tests whether a cached session is valid or not."""
        log.info(f"Checking session validity for session: {session.get_credentials().get_frozen_credentials().token}")
        # with self._lock:
        token = session.get_credentials().get_frozen_credentials().token
        if token in self._valid_tokens:
            log.info(f"Session with token: {token} has validity: {self._valid_tokens[token].is_valid()}")
            return self._valid_tokens[token].is_valid()
        else:
            try:
                log.info(f"Testing session with token: {token}")
                sts = session.client('sts')
                sts.get_caller_identity()
                self._valid_tokens[token] = SessionTokenCache(token=token)
                log.info("Adding session to cache, it's valid.")
                return True
            except ClientError:
                log.info("Session is invalid, returning false.")
                return False

    @abstractmethod
    def get_session(self, assumable_role: AssumableRole, prompt: bool, exit_on_fail=True) -> boto3.Session:
        pass

    def get_session_and_role(self, assumable_role: AssumableRole, prompt: bool, exit_on_fail=True) \
            -> Tuple[boto3.Session, AssumableRole]:
        return self.get_session(assumable_role, prompt, exit_on_fail), assumable_role

    @abstractmethod
    def cleanup_session_cache(self):
        pass

    def _get_user(self, prompt: bool) -> str:
        """
        Get the user either from cache, or prompt the user.

        Returns: str -> username
        """

        defaults = self._defaults
        if defaults is not None and not prompt:
            return defaults.user
        else:
            return Input.get_user(provider=self._defaults.provider.name)

    def _get_password(self, user_name, prompt: bool, save: bool = False) -> str:
        """
        Get the password either from keyring, or prompt the user.

        Returns: str -> password
        """

        password = self._secrets_mgr.get_password(user_name)
        reset_password = not password

        if reset_password or prompt:
            password = Input.get_password(provider=self._defaults.provider.name)
            if reset_password or save:
                self._secrets_mgr.set_password(user_name, password)

        return password
