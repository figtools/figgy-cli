DEFAULT_THREADS = 10

# Default configs around tuning.
AUDIT_SVC_MAX_THREADS = 15

POOLED_SVCS = [AUDIT_SVC_MAX_THREADS]

DYNAMO_DB_MAX_POOL_SIZE = int(max(POOLED_SVCS) * 1.1)


# Boto3 connection pools maintain an open file per connection in the pool. This can result in too many open
# files errors if we are caching too many Boto3 connections
MAX_OPEN_FILES = 130
MAX_CACHED_BOTO_POOLS = int(MAX_OPEN_FILES / DYNAMO_DB_MAX_POOL_SIZE / len(POOLED_SVCS))
