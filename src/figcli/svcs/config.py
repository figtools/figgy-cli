import json
import logging
import cachetools.func
from typing import Set, List, Tuple, Optional

from botocore.exceptions import ClientError
from cachetools import cached, TTLCache
from figgy.data.dao.audit import AuditDao
from figgy.data.dao.config import ConfigDao
from figgy.data.dao.replication import ReplicationDao
from figgy.data.dao.ssm import SsmDao
from figgy.data.models.config_item import ConfigState, ConfigItem
from figgy.models.fig import Fig
from figgy.models.replication_config import ReplicationConfig
from figgy.models.run_env import RunEnv
from figgy.svcs.fig_service import FigService

from figcli.config import PS_FIGGY_REPL_KEY_ID_PATH, PS_FIGGY_ALL_KMS_KEYS_PATH, PS_FIGGY_REGIONS
from figcli.models.kms_key import KmsKey
from figcli.svcs.cache_manager import CacheManager
from figcli.svcs.kms import KmsService
from figcli.utils.utils import Utils

log = logging.getLogger(__name__)


class ParameterUndecryptable(Exception):
    pass


class ConfigService:
    __CACHE_REFRESH_INTERVAL = 60 * 60 * 24 * 7 * 1000  # 1 week in MS
    """
    Service level class for interactive with config resources.

    Currently contains some business logic to leverage memory, filesystem, & remote (dynamodb)
    caches for the fastest possible lookup times.
    """
    _PS_NAME_CACHE_KEY = 'parameter_names'
    MEMORY_CACHED_NAMES: Set[str] = []
    MEMORY_CACHE_REFRESH_INTERVAL: int = 5000
    MEMORY_CACHE_LAST_REFRESH_TIME: int = 0
    DEFAULT_FIG_CACHE_DURATION: int = 60 * 60 * 24 * 7 * 1000  # 1 week in MS

    def __init__(self, config_dao: ConfigDao, ssm: SsmDao, replication_dao: ReplicationDao,
                 cache_mgr: CacheManager, kms_svc: KmsService, run_env: RunEnv):
        self._config_dao = config_dao
        self._cache_mgr = cache_mgr
        self._run_env = run_env
        self._repl = replication_dao
        self._ssm: SsmDao = ssm
        self._kms = kms_svc
        self._fig_svc: FigService = FigService(ssm)

    def get_root_namespaces(self) -> List[str]:
        all_params = self.get_parameter_names()
        return sorted(list(set([f"/{p.split('/')[1]}" for p in all_params])))

    @Utils.trace
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

    def get_fig(self, name: str, version: int = 0) -> Fig:
        """ Version is defaulted to 0, which will return latest. """
        fig = self._fig_svc.get(name, version)
        fig.is_repl_source = self.is_replication_source(name)
        fig.is_repl_dest = self.is_replication_destination(name)
        return fig

    def get_fig_simple(self, name: str) -> Fig:
        return self._fig_svc.get_simple(name)

    def get_fig_with_cache(self, name: str, cache_duration: int = DEFAULT_FIG_CACHE_DURATION):
        last_write, value = self._cache_mgr.get_or_refresh(name, self.get_fig_simple, name, max_age=cache_duration)
        return value

    def set_fig(self, fig: Fig):
        self._fig_svc.set(fig)

    @cachetools.func.ttl_cache(maxsize=256, ttl=30)
    def is_encrypted(self, name: str) -> bool:
        try:
            return self.get_fig(name).kms_key_id is not None
        except ClientError as e:
            # If we get a AccessDenied exception to decrypt this parameter, it must be encrypted
            if "AccessDeniedException" == e.response['Error']['Code'] and 'ciphertext' in f'{e}':
                return True

    @cachetools.func.ttl_cache(maxsize=256, ttl=15)
    def is_replication_source(self, name: str) -> bool:
        return bool(self._repl.get_cfgs_by_src(name))

    @cachetools.func.ttl_cache(maxsize=256, ttl=15)
    def is_replication_destination(self, name: str) -> bool:
        return bool(self._repl.get_config_repl(name))

    @cachetools.func.ttl_cache(maxsize=256, ttl=3600)
    def get_replication_key(self) -> str:
        return self._fig_svc.get_simple(PS_FIGGY_REPL_KEY_ID_PATH).value

    @cachetools.func.ttl_cache(maxsize=256, ttl=30)
    def get_replication_config(self, name: str) -> ReplicationConfig:
        return self._repl.get_config_repl(name)

    @cachetools.func.ttl_cache(maxsize=256, ttl=30)
    def get_replication_configs_by_source(self, name: str) -> List[ReplicationConfig]:
        return self._repl.get_cfgs_by_src(name)

    @cachetools.func.ttl_cache(maxsize=256, ttl=30)
    def get_all_encryption_keys(self) -> List[KmsKey]:
        keys: str = self._ssm.get_parameter(PS_FIGGY_ALL_KMS_KEYS_PATH)

        if not keys:
            raise ValueError(f"Required parameter {PS_FIGGY_ALL_KMS_KEYS_PATH} is missing!")
        else:
            key_aliases = json.loads(keys)
            return [KmsKey(alias=alias, id=self.get_kms_key_id(alias)) for alias in key_aliases]

    @cachetools.func.ttl_cache(maxsize=256, ttl=30)
    def get_all_regions(self) -> List[str]:
        return json.loads(self._ssm.get_parameter(PS_FIGGY_REGIONS))

    @cachetools.func.ttl_cache(maxsize=256, ttl=30)
    def get_kms_key_id(self, alias: str):
        key_path = f'/figgy/kms/{alias}-key-id'
        cache_key = f'kms-{alias}-{self._run_env.env}'
        es, key_id = self._cache_mgr.get_or_refresh(cache_key, self._ssm.get_parameter, key_path)
        return key_id

    def save(self, fig: Fig):
        log.info(f'Saving Fig: {fig}')
        self._fig_svc.save(fig)

    def delete(self, name: str):
        """
            If targeted configuration is a replication source throw error, you cannot delete repl sources.

            If this config is a repl destination, delete it, if not, try anyways, it's harmless & faster
            than checking first.
        """
        if self.is_replication_source(name):
            raise ValueError("Cannot delete fig, it is a source of replication!")

        # Todo: Wipe caches. Here
        self._repl.delete_config(name)
        self._fig_svc.delete(name)

    def decrypt(self, parameter_name: str, encrypted_data) -> str:
        return self._kms.safe_decrypt_parameter(parameter_name, encrypted_data)