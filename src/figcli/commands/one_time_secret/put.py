import string
import random

from prompt_toolkit.completion import WordCompleter

from figcli.commands.ots_context import OTSContext
from figcli.commands.types.one_time_secret import OTSCommand
from figcli.config import ots_put
from figcli.io.input import Input
from figcli.io.output import Output
from figcli.svcs.one_time_secret import OTSService
from figcli.utils.utils import Utils


class Put(OTSCommand):
    """
    Allows retrieval of a recently stored one-time-secret.
    """

    def __init__(self, ots_svc: OTSService, ots_context: OTSContext, colors_enabled: bool):
        super().__init__(ots_put, colors_enabled, ots_context)
        self._ots = ots_svc
        self._utils = Utils(colors_enabled)
        self._out = Output(colors_enabled)

    def _put(self):
        value = Input.input(f"Please input a value to share: ")

        # Safe convert to int or float, then validate
        expires_in_hours = Input.input(f"Select # of hours before value auto-expires: ", default="1")
        expires_in_hours = Utils.safe_cast(expires_in_hours, int, expires_in_hours)
        expires_in_hours = Utils.safe_cast(expires_in_hours, float, expires_in_hours)
        self._utils.validate(isinstance(expires_in_hours, int) or isinstance(expires_in_hours, float),
                             "You must provide a number of hours for when this secret should expire. No strings accepted.")
        self._utils.validate(expires_in_hours <= 48, "You may not specify an expiration time more than 48 hours in the future.")

        secret_id = self._ots.put_ots(value, expires_in_hours)
        self._out.print(f"\n\nTo share this secret, recipients will need the following")
        self._out.print(f"\n[[Secret Id]] -> {secret_id}")
        self._out.success(f"\n\nValue successfully stored, it will expire in {expires_in_hours} hours, or when retrieved.")

    def execute(self):
        self._put()
