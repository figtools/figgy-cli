import time
import os
import logging
import platform
import requests
from typing import List, Dict

from pydantic import BaseModel

from figcli.models.defaults.defaults import CLIDefaults
from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.setup import FiggySetup
from figcli.utils.utils import Utils
from concurrent.futures import ThreadPoolExecutor
from figcli.config import *

log = logging.getLogger(__name__)


class FiggyMetrics(BaseModel):
    COUNT_KEY = 'count'
    user_id: str
    metrics: Dict[str, Dict] = {}
    last_report: int = Utils.millis_since_epoch()

    def increment_count(self, command: str) -> None:
        metric = self.metrics.get(command, {})
        metric[self.COUNT_KEY] = metric.get(self.COUNT_KEY, 0) + 1
        self.metrics[command] = metric


class AnonymousUsageTracker:
    """`
    We want to track the usage counts of various commands and the version of Figgy people are currently using.
    This data will be valuable for informing future decisions & when considering upgrade paths or potentially
    introducing breaking changes and their impacts.
    """
    _CACHE_NAME = 'usage-metrics'
    _METRICS_KEY = 'metrics'
    _USER_KEY = 'user_id'
    _VERSION_KEY = 'version'
    _PLATFORM_KEY = 'platform'
    _COUNT_KEY = 'count'
    _DISABLE_METRICS_ENV_VAR = 'FIGGY_DISABLE_METRICS'

    REPORT_FREQUENCY = 1000 * 60 * 5  # Report every 5 minutes
    # REPORT_FREQUENCY = 1000 * 60 * 60 * 24  # Report daily

    @staticmethod
    def report_usage(metrics: FiggyMetrics):
        if os.environ.get(AnonymousUsageTracker._DISABLE_METRICS_ENV_VAR) == "true":
            return

        metrics_json = {AnonymousUsageTracker._METRICS_KEY: {}, AnonymousUsageTracker._USER_KEY: metrics.user_id}
        for key, val in metrics.metrics.items():
            metrics_json[AnonymousUsageTracker._METRICS_KEY][key] = val.get(AnonymousUsageTracker._COUNT_KEY, 0)

        metrics_json[AnonymousUsageTracker._VERSION_KEY] = VERSION
        metrics_json[AnonymousUsageTracker._PLATFORM_KEY] = platform.system()

        requests.post(url=FIGGY_LOG_METRICS_URL, json=metrics_json)

    @staticmethod
    def track_command_usage(function):
        """
        Tracks user command usage locally. This will be intermittently reported in aggregate.
        """

        def inner(self, *args, **kwargs):
            if os.environ.get(AnonymousUsageTracker._DISABLE_METRICS_ENV_VAR) == "true":
                return function(self, *args, **kwargs)    

            command = getattr(self, 'type', None)
            log.info(f'GOt command {command}')

            if command:
                command = command.name
                cache = CacheManager(AnonymousUsageTracker._CACHE_NAME)

                if hasattr(self, 'context') and hasattr(self.context, 'defaults') and self.context.defaults is not None:
                    if isinstance(self.context.defaults, CLIDefaults):
                        user_id = self.context.defaults.user_id
                    else:
                        user_id = "EmptyDefaults"
                else:
                    user_id = "NoOne"

                last_write, metrics = cache.get(AnonymousUsageTracker._METRICS_KEY,
                                                default=FiggyMetrics(user_id=user_id))

                metrics.increment_count(command)
                if Utils.millis_since_epoch() - metrics.last_report > AnonymousUsageTracker.REPORT_FREQUENCY:
                    defaults = FiggySetup.stc_get_defaults(skip=True)
                    if defaults and defaults.usage_tracking:
                        # Ship it async. If it don't worky, oh well :shruggie:
                        with ThreadPoolExecutor(max_workers=1) as pool:
                            pool.submit(AnonymousUsageTracker.report_usage, metrics)
                            log.info(f'Reporting anonymous usage for metrics: {metrics}')
                            cache.write(AnonymousUsageTracker._METRICS_KEY, FiggyMetrics(user_id=user_id))
                            return function(self, *args, **kwargs)
                else:
                    cache.write(AnonymousUsageTracker._METRICS_KEY, metrics)

            return function(self, *args, **kwargs)

        return inner
