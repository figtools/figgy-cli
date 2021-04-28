import os
import getpass
from keyrings.alt.file import EncryptedKeyring


class FiggyKeyring(EncryptedKeyring):
    _KEYRING_PASSWORD_ENV_VAR = 'FIGGY_KEYRING_PASSWORD'

    def _unlock(self):
        """
        Unlock this keyring by getting the password for the keyring from the
        user.
        """
        keyring_password = os.environ.get(FiggyKeyring._KEYRING_PASSWORD_ENV_VAR)
        if keyring_password:
            self.keyring_key = keyring_password
        else:
            print(f"You may avoid unlock prompts by setting the environment variable:"
                  f" `{FiggyKeyring._KEYRING_PASSWORD_ENV_VAR}` to your keyring password.")
            self.keyring_key = getpass.getpass('Please enter password for encrypted keyring: ')
        try:
            ref_pw = self.get_password('keyring-setting', 'password reference')
            assert ref_pw == 'password reference value'
        except AssertionError:
            self._lock()
            raise ValueError("Incorrect Password")

    def _init_file(self):
        """
        Initialize a new password file and set the reference password.
        """
        self.keyring_key = os.environ.get(FiggyKeyring._KEYRING_PASSWORD_ENV_VAR)

        if not self.keyring_key:
            self.keyring_key = self._get_new_password()

        # set a reference password, used to check that the password provided
        #  matches for subsequent checks.
        self.set_password(
            'keyring-setting', 'password reference', 'password reference value'
        )
        self._write_config_value('keyring-setting', 'scheme', self.scheme)
        self._write_config_value('keyring-setting', 'version', self.version)