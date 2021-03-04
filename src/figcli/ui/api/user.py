from abc import ABC

from figcli.commands.config_context import ConfigContext
from figcli.ui.controller import Controller
from figcli.ui.models.user import User
from figcli.ui.route import Route


class UserController(Controller, ABC):

    def __init__(self, prefix: str, config_context: ConfigContext):
        super().__init__(prefix)
        self.context: ConfigContext = config_context
        self._routes.append(Route('/user', self.get_user, ["GET"]))
        self.user = User(name=self.context.defaults.user,
                         role=self.context.defaults.role,
                         assumable_roles=self.context.defaults.assumable_roles)

    def get_user(self):
        return self.user.dict()
