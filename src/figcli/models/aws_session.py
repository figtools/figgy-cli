import datetime
import time
import logging
from typing import Dict


# Todo add support for expiration and check for expiration rather than calling STS with session.
from pydantic import BaseModel, Field, validator

# This is in the "expiration" window if it's within 10M of it's expiration time.
EXPIRATION_WINDOW = 60 * 10

log = logging.getLogger(__name__)

class FiggyAWSSession(BaseModel):

    access_key: str = Field(None, alias="AccessKeyId")
    secret_key: str = Field(None, alias="SecretAccessKey")
    token: str = Field(None, alias="SessionToken")
    expiration: int = Field(0, alias="Expiration")

    @validator('expiration', pre=True)
    def set_expiration(cls, value):
        return value.timestamp()

    # @staticmethod
    # def from_sts_response(response: Dict) -> "FiggyAWSSession":
    #     creds = response.get('Credentials', {})
    #
    #     return FiggyAWSSession(
    #         access_key=creds.get('AccessKeyId'),
    #         secret_key=creds.get('SecretAccessKey'),
    #         token=creds.get('SessionToken'),
    #         expiration=creds.get('Expiration').timestamp()
    #     )

    def expires_soon(self):
        # log.info(f"Returning expires soon: {time.time() + EXPIRATION_WINDOW > self.expiration} -- expiration is in {self.expiration - time.time()} seconds.")
        return time.time() + EXPIRATION_WINDOW > self.expiration



"""
Example STS boto response:

{
    'Credentials': {
        'AccessKeyId': 'string',
        'SecretAccessKey': 'string',
        'SessionToken': 'string',
        'Expiration': datetime(2015, 1, 1)
    },
    'AssumedRoleUser': {
        'AssumedRoleId': 'string',
        'Arn': 'string'
    },
    'PackedPolicySize': 123
}
"""
