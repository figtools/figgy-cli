from typing import Union

from figcli.commands.factory import Factory
from figcli.commands.figgy_context import FiggyContext
from figcli.models.defaults.defaults import CLIDefaults
from figcli.models.defaults.provider import Provider
from figcli.svcs.auth.google.google_session_provider import GoogleSessionProvider
from figcli.svcs.auth.bastion.bastion_session_provider import BastionSessionProvider
from figcli.svcs.auth.okta.okta_session_provider import OktaSessionProvider
from figcli.svcs.auth.profile.profile_session_provider import ProfileSessionProvider
from figcli.svcs.auth.provider.session_provider import SessionProvider
from figcli.svcs.auth.provider.sso_session_provider import SSOSessionProvider
from figcli.svcs.auth.unselected.unselected_session_provider import UnselectedSessionProvider


class SessionProviderFactory(Factory):

    def __init__(self, defaults: CLIDefaults, context: FiggyContext):
        self._defaults = defaults
        self._context = context
        self.__bastion_session_provider = None
        self.__okta_session_provider = None
        self.__google_session_provider = None
        self.__profile_provider = None

    def instance(self) -> Union[SSOSessionProvider, SessionProvider]:
        if self._defaults.provider is Provider.OKTA:
            if not self.__okta_session_provider:
                self.__okta_session_provider = OktaSessionProvider(self._defaults, self._context)

            return self.__okta_session_provider
        elif self._defaults.provider is Provider.AWS_BASTION:
            if not self.__bastion_session_provider:
                self.__bastion_session_provider = BastionSessionProvider(self._defaults, self._context)

            return self.__bastion_session_provider
        elif self._defaults.provider is Provider.GOOGLE:
            if not self.__google_session_provider:
                self.__google_session_provider = GoogleSessionProvider(self._defaults, self._context)

            return self.__google_session_provider
        elif self._defaults.provider is Provider.PROFILE:
            if not self.__profile_provider:
                self.__profile_provider = ProfileSessionProvider(self._defaults, self._context)

            return self.__profile_provider
        elif self._defaults.provider is Provider.UNSELECTED:
            return UnselectedSessionProvider(self._defaults, self._context)
        else:
            raise NotImplementedError(f"Provider: {self._defaults.provider} is not currently supported.")
