import os

from figcli.config import FIGGY_TESTS_ENABLED
from figcli.io.output import Output
from figcli.models.defaults.defaults import CLIDefaults, RESTRICTED_ENV_VARS
from figcli.models.defaults.provider import Provider
from figcli.utils.utils import Utils


class EnvironmentValidator:
    """
    Houses genric environment validation logic that may branch based on current
    configurations, such as Bastion / OKTA / GOOGLE / ETC.
    """

    def __init__(self, defaults: CLIDefaults):
        self._defaults = defaults
        self._out = Output(self._defaults.colors_enabled)
        self._utils = Utils(self._defaults.colors_enabled)

    def validate_all(self):
        if self._defaults.provider == Provider.AWS_BASTION:
            self.validate_environment_variables()

        return self

    def validate_environment_variables(self):
        # If figgy is operating in a TEST environment, ignore this.
        if os.environ.get(FIGGY_TESTS_ENABLED):
            return self

        invalid_vars = []

        for env_var in RESTRICTED_ENV_VARS:
            if os.environ.get(env_var):
                invalid_vars.append(env_var)

        if invalid_vars:
            self._out.error_h2(f'AWS Environment overrides detected.\n\n {invalid_vars} is currently set in your '
                               f'environment. AWS_* prefixed environment variables can interfere with figgy '
                               f'operations and may cause unpredictable behavior. Please unset all AWS_ prefixed ENV '
                               f'variables before continuing.')

            self._out.print('\nTo unset the problematic variables, please run the following command(s) in your shell: '
                            '\n')
            for var in invalid_vars:
                self._out.print(f'unset {var}')

            self._utils.error_exit("Invalid environment detected, exiting.")

        return self
