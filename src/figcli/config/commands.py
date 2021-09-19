from pathlib import Path
from figcli.config.aws import *
from figcli.config.constants import *
from figcli.models.cli_command import CliCommand

# Root subcommand types
version = CliCommand("version")
command = CliCommand('command')
resource = CliCommand('resource')
configure = CliCommand('configure')
ui = CliCommand('ui')

# Resource types
config = CliCommand('config')
iam = CliCommand('iam')
login = CliCommand('login')
ots = CliCommand('ots')

resources = {config, iam, login, ui, ots}

# Config Sub Command definitions
sync = CliCommand('sync')
put = CliCommand('put')
restore = CliCommand('restore')
point_in_time = CliCommand('point-in-time')
delete = CliCommand('delete')
prune = CliCommand('prune')
get = CliCommand('get')
edit = CliCommand('edit')
list_com = CliCommand('list')
share = CliCommand('share')
promote = CliCommand('promote')
ci_path = CliCommand('config')
info = CliCommand('info')
browse = CliCommand('browse')
prompt_com = CliCommand('prompt')
audit = CliCommand('audit')
dump = CliCommand('dump')
replication_only = CliCommand('replication-only')
manual = CliCommand('manual')
env = CliCommand('env')
prefix = CliCommand('prefix')
out = CliCommand('out')
skip_upgrade = CliCommand('skip-upgrade')
service = CliCommand('service')
debug = CliCommand('debug')
copy_from = CliCommand('copy-from')
generate = CliCommand('generate')
from_path = CliCommand('from')
validate = CliCommand('validate')
profile = CliCommand('profile')
build_cache = CliCommand('build-cache')

# IAM sub commands
export = CliCommand('export')
iam_restore = CliCommand('restore', hash_key='iam_restore')

# UI subcommands
run = CliCommand('run')

# OTS subcommands
ots_get = CliCommand('get')
ots_put = CliCommand('put')

all_profiles = CliCommand('all-profiles')
role = CliCommand('role')
# argparse options
help = CliCommand('help')
required = CliCommand('required')
action = CliCommand('action')
store_true = 'store_true'


# help commands
sandbox = CliCommand('sandbox')
upgrade = CliCommand('upgrade')

# Maps CLI `--options` for each argument, and sets flags if necessary
arg_options = {
    ui: {
        run: {
            info: {action: store_true, required: False},
            env: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        }
    },
    config: {
        prune: {
            config: {action: None, required: False},
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        delete: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        get: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        list_com: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        put: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        edit: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        restore: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            point_in_time: {action: store_true, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        share: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        sync: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            replication_only: {action: store_true, required: False},
            config: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            copy_from: {action: None, required: False},
            profile: {action: None, required: False},
        },
        browse: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            prefix: {action: None, required: False},
            profile: {action: None, required: False},
        },
        dump: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            prefix: {action: None, required: False},
            out: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        audit: {
            info: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        promote: {
            info: {action: store_true, required: False},
            env: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
        },
        generate: {
            info: {action: store_true, required: False},
            env: {action: None, required: False},
            from_path: {action: None, required: False},
            role: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        validate: {
            info: {action: store_true, required: False},
            prompt_com: {action: store_true, required: False},
            env: {action: None, required: False},
            config: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        build_cache: {
            info: {action: store_true, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        }
    },
    iam: {
        export: {
            info: {action: store_true, required: False},
            env: {action: None, required: False},
            skip_upgrade: {action: store_true, required: False},
            all_profiles: {action: store_true, required: False},
            role: {action: None, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        iam_restore: {
            info: {action: store_true, required: False},
            debug: {action: store_true, required: False},
        },
    },
    login: {
        login: {
            info: {action: store_true, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        sandbox: {
            info: {action: store_true, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            role: {action: None, required: False},
        }
    },
    ots: {
        ots_get: {
            info: {action: store_true, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        },
        ots_put: {
            info: {action: store_true, required: False},
            skip_upgrade: {action: store_true, required: False},
            debug: {action: store_true, required: False},
            profile: {action: None, required: False},
        }
    },
}

# Merge key suffixes
merge_uri_suffix = ":uri"
empty_uri_suffix = ''
merge_suffixes = [merge_uri_suffix, empty_uri_suffix]

# Supported commands by resource
config_commands = [sync, put, edit, delete, prune, get, share, generate,
                   list_com, browse, audit, dump, restore, promote, validate, build_cache]
iam_commands = [export, iam_restore]
help_commands = [configure, login, sandbox, role]
maintenance_commands = [version, upgrade]
login_commands = [login, sandbox]
ui_commands = [ui]
ots_commands = [ots_get, ots_put]

all_commands = iam_commands + help_commands + config_commands + login_commands + ui_commands

# Used to build out parser, map of resource to sub-commands
resource_map = {
    config: config_commands,
    iam: iam_commands,
    login: login_commands,
    ui: [run],
    ots: ots_commands
}

options = {ci_path,  info}


# KMS Key Types / Mapping
kms_app = 'app'
kms_data = 'data'
kms_devops = 'devops'
kms_keys = [kms_app, kms_data, kms_devops]

# Validation Supported types
plugin = "plugin"
cve = "cve"

# Command to option requirement map
REQ_OPTION_MAP = {
    prune: [ci_path],
    delete: [],
    get: [],
    list_com: [],
    put: [],
    restore: [],
    share: [],
    sync: [ci_path],
    edit: [],
    generate: [ci_path]
}
