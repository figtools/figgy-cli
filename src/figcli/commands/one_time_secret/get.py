from figcli.commands.ots_context import OTSContext
from figcli.commands.types.one_time_secret import OTSCommand
from figcli.config import ots_get
from figcli.io.input import Input
from figcli.io.output import Output
from figcli.svcs.one_time_secret import OTSService
from figcli.utils.utils import Utils


class Get(OTSCommand):
    """
    Allows retrieval of a recently stored one-time-secret.
    """

    def __init__(self, ots_svc: OTSService, ots_context: OTSContext, colors_enabled: bool):

        super().__init__(ots_get, colors_enabled, ots_context)
        self._ots = ots_svc
        self._utils = Utils(colors_enabled)
        self._out = Output(colors_enabled)

    def _get(self):
        secret_id = Input.input("Please input the secret id you wish to fetch: ")
        self._utils.validate("--" in secret_id, "Provided secret id is not a valid format.")
        self._utils.validate(len(secret_id.split("--")) == 2, "Provided secret id is not a valid format.")

        value = self._ots.get_ots(secret_id)

        if value:
            self._out.print(f"\n[[Retrieved Value:]] {value}")
            self._out.warn(f"\nThis value has been deleted and can no longer be retrieved.")
        else:
            self._out.warn(f"\nThe value associated with the provided ID does not exist, has already been retrieved, "
                           f"or has expired.")

    def execute(self):
        self._get()
