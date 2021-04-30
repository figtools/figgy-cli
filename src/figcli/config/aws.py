DEFAULT_SESSION_DURATION = 43200  # 12 hours
SANDBOX_SESSION_DURATION = 60 * 60 # 1 hour

BASTION_PROFILE_ENV_NAME = 'FIGGY_AWS_PROFILE'

AWS_REGIONS = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'af-south-1', 'ap-east-1', 'ap-east-2',
               'ap-northeast-3', 'ap-northeast-2', 'ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2',
               'ca-central-1', 'cn-north-1', 'cn-northwest-1', 'eu-central-1', 'eu-west-1', 'eu-west-2',
               'eu-west-3', 'eu-north-1', 'me-south-1', 'sa-east-1', 'us-gov-east-1', 'us-gov-west-1']

AWS_CFG_ACCESS_KEY_ID = 'aws_access_key_id'
AWS_CFG_SECRET_KEY = 'aws_secret_access_key'
AWS_CFG_TOKEN = 'aws_session_token'
AWS_CFG_REGION = 'region'
AWS_CFG_OUTPUT = 'output'


RESTRICTED_ENV_VARS = ['AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION', 'AWS_PROFILE', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']