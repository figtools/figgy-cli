import os
import threading
from json import JSONDecodeError
from typing import List, Optional

import boto3
import logging
import base64
import json
from abc import ABC, abstractmethod

from botocore.exceptions import NoCredentialsError, ParamValidationError, ClientError
from filelock import FileLock

from figcli.commands.figgy_context import FiggyContext
from figcli.config import *
from figcli.models.assumable_role import AssumableRole
from figcli.models.aws_session import FiggyAWSSession
from figcli.models.defaults.defaults import CLIDefaults
from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.auth.provider.session_provider import SessionProvider
from figcli.svcs.vault import FiggyVault
from figcli.ui.models.global_environment import GlobalEnvironment
from figcli.utils.secrets_manager import SecretsManager
from figcli.utils.utils import InvalidSessionError, Utils

log = logging.getLogger(__name__)


class SSOSessionProvider(SessionProvider, ABC):
    _MAX_ATTEMPTS = 5

    def __init__(self, defaults: CLIDefaults, context: FiggyContext):
        super().__init__(defaults, context)
        self._utils = Utils(defaults.colors_enabled)
        self._sts = boto3.client('sts')
        self._context = context
        keychain_enabled = defaults.extras.get(DISABLE_KEYRING) is not True
        vault = FiggyVault(keychain_enabled=keychain_enabled, secrets_mgr=self._secrets_mgr)
        self._sts_cache: CacheManager = CacheManager(file_override=STS_SESSION_CACHE_PATH, vault=vault)
        self._saml_cache: CacheManager = CacheManager(file_override=SAML_SESSION_CACHE_PATH, vault=vault)

    @abstractmethod
    def get_assumable_roles(self) -> List[AssumableRole]:
        pass

    @abstractmethod
    def cleanup_session_cache(self):
        pass

    @abstractmethod
    def get_saml_assertion(self, prompt: bool = False, mfa: Optional[str] = None):
        pass

    def get_session(self, env: GlobalEnvironment, prompt: bool, exit_on_fail=True, mfa: Optional[str] = None) -> boto3.Session:
        """
        Creates a session in the specified ENV for the target role from a SAML assertion returned by SSO authentication.
        Args:
            assumable_role: AssumableRole - The role to be leveraged to authenticate this session
            prompt: If prompt is set, we will not use a cached session and will generate new sessions for okta and mgmt.
            exit_on_fail: Exit the program if this session hydration fails.
            mfa: MFA to use with authentication attempt.

        returns: Hydrated session for role + account that match the specified one in the provided AssumableRole
        """

        log.info(f"Getting session, was provided MFA: {mfa}")

        # Prevent multiple requests from differing threads all generating new sessions / authing at the same time.
        # Sessions are encrypted and cached in the lockbox, so we want to re-auth once, then read from the lockbox.
        # This cannot be an instance variable, it does not work properly evne though there is only one instantiated
        # SSOSessionProvider
        lock = FileLock(f'{SAML_SESSION_CACHE_PATH}-provider.lock')
        with lock:
            log.info(f"Got lock: {SAML_SESSION_CACHE_PATH}-provider.lock")
            role_arn = f"arn:aws:iam::{env.role.account_id}:role/{env.role.role.full_name}"
            principal_arn = f"arn:aws:iam::{env.role.account_id}:saml-provider/{env.role.provider_name}"
            forced = False
            log.info(f"Getting session for role: {role_arn} in env: {env.role.run_env.env} "
                     f"with principal: {principal_arn}")
            attempts = 0
            while True:
                try:
                    if prompt and not forced:
                        forced = True
                        raise InvalidSessionError("Forcing new session due to prompt.")

                    # One role can create N sessions across N regions.
                    creds: FiggyAWSSession = self._sts_cache.get_val(env.role.cache_key())
                    log.debug(f"Got creds from cache: {creds} when searching for env: {env}")

                    if creds:
                        session = boto3.Session(
                            aws_access_key_id=creds.access_key,
                            aws_secret_access_key=creds.secret_key,
                            aws_session_token=creds.token,
                            region_name=env.region
                        )

                        if creds.expires_soon() or not self._is_valid_session(session):
                            self._utils.validate(attempts < self._MAX_ATTEMPTS,
                                                 f"Failed to authenticate with AWS after {attempts} attempts. Exiting.")

                            attempts = attempts + 1
                            log.info("Invalid session detected in cache. Raising session error.")
                            raise InvalidSessionError("Invalid Session Detected")

                        log.info("Valid SSO session returned from cache.")
                        return session
                    else:
                        raise InvalidSessionError("Forcing new session, cache is empty.")
                except (FileNotFoundError, JSONDecodeError, NoCredentialsError, InvalidSessionError) as e:
                    log.info(f"SessionProvider -- got expected error: {e}")
                    try:
                        # Todo Remove requiring raw saml and instead work with b64 encoded saml?
                        try:
                            assertion: str = self._saml_cache.get_val_or_refresh(SAML_ASSERTION_CACHE_KEY,
                                                                                 self.get_saml_assertion, (prompt, mfa),
                                                                                 max_age=SAML_ASSERTION_MAX_AGE)
                            encoded_assertion = base64.b64encode(assertion.encode('utf-8')).decode('utf-8')
                            response = self._sts.assume_role_with_saml(RoleArn=role_arn,
                                                                       PrincipalArn=principal_arn,
                                                                       SAMLAssertion=encoded_assertion,
                                                                       DurationSeconds=3500)
                        except ClientError:
                            log.info("Refreshing SAML assertion, auth failed with cached or refreshed version.")
                            assertion = self.get_saml_assertion(prompt, mfa=mfa)
                            encoded_assertion = base64.b64encode(assertion.encode('utf-8')).decode('utf-8')
                            response = self._sts.assume_role_with_saml(RoleArn=role_arn,
                                                                       PrincipalArn=principal_arn,
                                                                       SAMLAssertion=encoded_assertion,
                                                                       DurationSeconds=3500)

                        # response['Credentials']['Expiration'] = "cleared"
                        session = FiggyAWSSession(**response.get('Credentials', {}))
                        self._saml_cache.write(SAML_ASSERTION_CACHE_KEY, assertion)
                        self._sts_cache.write(env.role.cache_key(), session)
                    except (ClientError, ParamValidationError) as e:
                        if isinstance(e, ParamValidationError) or "AccessDenied" == e.response['Error']['Code']:
                            if exit_on_fail:
                                self._utils.error_exit(f"Error authenticating with AWS from SAML Assertion: {e}")
                        else:
                            if exit_on_fail:
                                print(e)
                                self._utils.error_exit(
                                    f"Error getting session for role: {role_arn} -- Are you sure you have permissions?")

                        raise e
