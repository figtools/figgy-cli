import logging
from functools import cache, lru_cache
from typing import Set, List, Tuple, Optional

import cachetools as cachetools
from botocore.exceptions import ClientError
from cachetools import cached, TTLCache

from figgy.data.dao.config import ConfigDao
from figgy.data.dao.ssm import SsmDao
from figgy.data.models.config_item import ConfigState, ConfigItem
from figgy.models.run_env import RunEnv
from figgy.models.fig import Fig
from figgy.svcs.fig_service import FigService

from figcli.svcs.cache_manager import CacheManager
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class ParameterUndecryptable(Exception):
    pass


# Todo, lots more from SSMDao should be moved here.
class ConfigService:
    __CACHE_REFRESH_INTERVAL = 60 * 60 * 24 * 7 * 1000  # 1 week in MS
    """
    Service level class for interactive with config resources.

    Currently contains some business logic to leverage a both local (filesystem) & remote (dynamodb)
    cache for the fastest possible lookup times.
    """
    _PS_NAME_CACHE_KEY = 'parameter_names'
    MEMORY_CACHED_NAMES: Set[str] = []
    MEMORY_CACHE_REFRESH_INTERVAL: int = 5000
    MEMORY_CACHE_LAST_REFRESH_TIME: int = 0

    def __init__(self, config_dao: ConfigDao, ssm: SsmDao, cache_mgr: CacheManager, run_env: RunEnv):
        self._config_dao = config_dao
        self._cache_mgr = cache_mgr
        self._run_env = run_env
        self._ssm: SsmDao = ssm
        self._fig_svc: FigService = FigService(ssm)

    def get_root_namespaces(self) -> List[str]:
        all_params = self.get_parameter_names()
        return sorted(list(set([f"/{p.split('/')[1]}" for p in all_params])))

    @Utils.trace
    @cached(TTLCache(maxsize=10, ttl=5))
    def get_parameter_names(self) -> Set[str]:
        """
        Looks up local cached configs, then queries new config names from the remote cache, merges the two, and
        finally updates the local cache. This ensures very fast bootstrap times b/c querying thousands of parameter
        names from a remote cache can a bit too much time. `figgy` does not accept slow performance.

        :return: Set[str] names of all configs stored in ParameterStore.
        """
        cache_key = f'{self._run_env.env}-{self._PS_NAME_CACHE_KEY}'

        # Find last cache full refresh date
        last_refresh = self._cache_mgr.last_refresh(cache_key)

        # Do a full refresh if cache is too old.
        if Utils.millis_since_epoch() - last_refresh > self.__CACHE_REFRESH_INTERVAL:
            configs: Set[ConfigItem] = self._config_dao.get_config_names_after(0)
            all_parameters: Set[str] = set([x.name for x in configs if x.state == ConfigState.ACTIVE])
            self._cache_mgr.write(cache_key, all_parameters)
        else:

            # Get items from cache
            last_write, cached_contents = self._cache_mgr.get(cache_key)

            # Find new items added to remote cache table since last local cache write
            updated_items: Set[ConfigItem] = self._config_dao.get_config_names_after(last_write)

            # Add new names to cache
            added_names, deleted_names = set(), set()
            for item in updated_items:
                if item.state is ConfigState.ACTIVE:
                    added_names.add(item.name)
                elif item.state is ConfigState.DELETED:
                    deleted_names.add(item.name)
                else:
                    # Default to add if no state set
                    added_names.add(item.name)

            self._cache_mgr.append(cache_key, added_names)
            self._cache_mgr.delete(cache_key, deleted_names)

            log.debug(f"Cached: {cached_contents}")
            log.debug(f"Cached: {deleted_names}")
            log.debug(f"Cached: {added_names}")

            all_parameters = set(cached_contents) - deleted_names | added_names

        return all_parameters

    def get_parameter_names_by_filter(self, filter_str: str):
        return filter(lambda x: filter_str in x, self.get_parameter_names())

    def get_parameter_with_description(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns a parameter's value and description from its provided name. Returns `None, None` tuple
        if no parameter exists.

        This method paginates to the last page via the SSM API then grabs the last item, which will
        be the current version.

        :param name: The name of the parameter - e.g. /app/foo/bar
        :return: Tuple[value, description] - Value & Description found. None returned if no parameter exists.
        """
        try:
            return self._ssm.get_parameter_with_description(name)
        except ClientError as e:
            if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                raise ParameterUndecryptable(f'{e}')

    def get_fig(self, name: str) -> Fig:
        fig = self._fig_svc.get(name)
        fig.is_repl_source = self.is_replication_source(name)
        fig.is_repl_dest = self.is_replication_destination(name)
        return fig

    def get_fig_simple(self, name: str) -> Fig:
        return self._fig_svc.get_simple(name)

    def set_fig(self, fig: Fig):
        self._fig_svc.set(fig)

    @cached(TTLCache(maxsize=1024, ttl=30))
    def is_encrypted(self, name: str) -> bool:
        try:
            return self.get_fig(name).kms_key_id is not None
        except ClientError as e:
            # If we get a AccessDenied exception to decrypt this parameter, it must be encrypted
            if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                return True

    @cached(TTLCache(maxsize=1024, ttl=120))
    def is_replication_source(self, name: str) -> bool:
        return bool(self._config_dao.get_cfgs_by_src(name))

    @cached(TTLCache(maxsize=1024, ttl=120))
    def is_replication_destination(self, name: str) -> bool:
        return bool(self._config_dao.get_config_repl(name))

    def save(self, fig: Fig):
        self._fig_svc.save(fig)

