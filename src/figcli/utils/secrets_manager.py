from figcli.svcs.secrets.figgy_keyring import FiggyKeyring
from figcli.utils.utils import *
import platform
import keyring
import pyotp
from figcli.config import *
from keyring.backends.OS_X import Keyring
from keyring.backends.Windows import WinVaultKeyring
from keyrings.alt.file import EncryptedKeyring, PlaintextKeyring
import os


class SecretsManager:

    def __init__(self):
        self._last_token = 9999999999
        self._keyring_pw = None
        self.set_keyring()

    def set_keyring(self):
        if platform.system() == WINDOWS:
            keyring.set_keyring(WinVaultKeyring())
        elif os.environ.get(OVERRIDE_KEYRING_ENV_VAR) == "true":  # Used in builds when running tests
            keyring.set_keyring(PlaintextKeyring())
        elif platform.system() == MAC:
            keyring.set_keyring(keyring.backends.OS_X.Keyring())
        elif platform.system() == LINUX:
            keyring.set_keyring(FiggyKeyring())
        else:
            Utils.stc_error_exit("Only OSX and MAC and Linux with installed SecretStorage are supported for "
                                 "OKTA + Keyring integration.")

    def get_next_mfa(self, user):
        token = self.generate_mfa(user)
        while token == self._last_token:
            print(f"Last token {self._last_token} has been used, waiting for new MFA token...")
            time.sleep(3)
            token = self.generate_mfa(user)

        self._last_token = token
        return token

    def get_mfa_password(self, user: str):
        mfa_override = os.environ.get(FIGGY_MFA_SECRET_OVERRIDE)

        if mfa_override:
            return mfa_override
        else:
            return keyring.get_password(FIGGY_KEYRING_NAMESPACE, f'{user}-mfa')

    def generate_mfa(self, user: str) -> str:
        mfa_secret = self.get_mfa_password(user)
        token = pyotp.TOTP(mfa_secret).now()
        print(f"Authenticating with one-time token: {token}")
        return token

    def set_mfa_secret(self, user: str, mfa_secret: str):
        keyring.set_password(FIGGY_KEYRING_NAMESPACE, f'{user}-mfa', mfa_secret)

    def set_password(self, user: str, password: str) -> None:
        keyring.set_password(FIGGY_KEYRING_NAMESPACE, user, password)

    def get_or_set(self, user: str, backup: str):
        current = self.get_password(user)
        if not current:
            self.set_password(user, backup)

        return current

    def get_encryption_key(self):
        return keyring.get_password(FIGGY_KEYRING_NAMESPACE, KEYCHAIN_ENCRYPTION_KEY)

    def set_encryption_key(self, encryption_key: str):
        self.set_password(KEYCHAIN_ENCRYPTION_KEY, encryption_key)

    def get_password(self, user: str) -> str:
        pw_override = os.environ.get(FIGGY_PASSWORD_OVERRIDE)
        if pw_override:
            return pw_override
        else:
            return keyring.get_password(FIGGY_KEYRING_NAMESPACE, user)
