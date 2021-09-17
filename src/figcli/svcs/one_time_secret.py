import base64
import datetime
import random
import string
from typing import Optional, Union

from figgy.data.dao.kms import KmsDao
from figgy.data.dao.ssm import SsmDao

from figcli.config import PS_FIGGY_OTS_KEY_ID


class OTSService:
    """
    Contains service methods for one-time-secret generation / retrieval / cleanup, etc.
    """
    KEY_LENGTH = 20
    DEFAULT_DESCRIPTION = 'One-time password. This will disappear soon.'
    OTS_NAMESPACE = '/figgy/ots'

    def __init__(self, ssm: SsmDao, kms: KmsDao, kms_id: str):
        self._ssm = ssm
        self._kms = kms
        self.kms_id = kms_id

    def get_ots(self, secret_id: str) -> Optional[str]:
        """
        Takes a one-time-secret name and its associated password and returns the associated value (if it exists).
        """

        key, password = tuple(secret_id.split("--"))
        param_name: str = f'{self.OTS_NAMESPACE}/{key}'
        encrypted_str_value = self._ssm.get_parameter(param_name)
        if encrypted_str_value:
            b64_encoded_value = encrypted_str_value.encode('utf-8')
            value = self._kms.decrypt(b64_encoded_value, encryption_password=password)
            self._ssm.delete_parameter(param_name)
            return value
        else:
            return None

    def put_ots(self, value: str, expires_in_hours: Union[int, float] = 1) -> str:
        """
        Takes a one-time-secret name, value, and password and encrypts and stores the one-time-secret.

        returns: secret_id
        """
        secret_id = ''.join(random.choice(string.ascii_lowercase) for i in range(14))
        password = ''.join(random.choice(string.ascii_lowercase) for i in range(14))
        param_name: str = f'{self.OTS_NAMESPACE}/{secret_id}'
        encrypted_value = self._kms.encrypt(self.kms_id, value, password)
        b64_encoded_value = base64.b64encode(encrypted_value)
        decoded_str = b64_encoded_value.decode('utf-8')

        now = datetime.datetime.utcnow()
        future_date = now + datetime.timedelta(hours=expires_in_hours)

        expiration_policy = {
            "Type": "Expiration",
            "Version": "1.0",
            "Attributes": {
                "Timestamp": future_date.isoformat()[:-3] + 'Z'
            }
        }

        self._ssm.set_parameter(param_name, decoded_str, self.DEFAULT_DESCRIPTION, policies=[expiration_policy])

        return f'{secret_id}--{password}'
