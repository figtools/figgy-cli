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