import base64

from figgy.data.dao.kms import KmsDao
from figgy.data.dao.ssm import SsmDao

from figcli.utils.utils import *


class KmsService:
    """
    Provides access to KMS apis
    """

    def __init__(self, kms_dao: KmsDao, ssm_dao: SsmDao):
        self._kms = kms_dao
        self._ssm = ssm_dao
        self.account_id = self._ssm.get_parameter(ACCOUNT_ID_PATH)
        self.region = self._ssm.get_parameter(REGION_PATH)

    def decrypt(self, base64_ciphertext) -> str:
        return self._kms.decrypt(base64_ciphertext)

    def decrypt_with_context(self, base64_ciphertext, context: Dict):
        return self._kms.decrypt_with_context(base64_ciphertext, context)

    def decrypt_parameter(self, parameter_name, encrypted_value: str):
        parameter_arn = f"arn:aws:ssm:{self.region}:{self.account_id}:parameter{parameter_name}"

        return self.decrypt_with_context(encrypted_value, {"PARAMETER_ARN": parameter_arn})

    def safe_decrypt_parameter(self, parameter_name: str, encrypted_value: str):
        try:
            return self.decrypt_parameter(parameter_name, encrypted_value)
        except Exception as e:
            return encrypted_value

    def encrypt(self, value: str, encryption_context: str):
        self._kms.encrypt()