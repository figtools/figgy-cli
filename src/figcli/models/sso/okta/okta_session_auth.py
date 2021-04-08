from figcli.models.defaults.defaults import CLIDefaults
from figcli.models.sso.okta.okta_auth import OktaAuth
from figcli.models.sso.okta.okta_session import OktaSession


class OktaSessionAuth(OktaAuth):
    def __init__(self, defaults: CLIDefaults, session: OktaSession):
        super().__init__(defaults)
        self.session = session

    def get_session(self):
        return self.session
