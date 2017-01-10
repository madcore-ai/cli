from __future__ import unicode_literals

FOLLOWME_STACK_NAME = 'MADCORE-FollowMe'
S3_STACK_NAME = 'MADCORE-S3'
NETWORK_STACK_NAME = 'MADCORE-Net'
CORE_STACK_NAME = 'MADCORE-Core'
CLUSTER_STACK_NAME = 'MADCORE-Cluster'
DNS_STACK_NAME = 'MADCORE-Dns'

# used to load parameters files
STACK_SHORT_NAMES = {
    'sgfm': FOLLOWME_STACK_NAME,
    's3': S3_STACK_NAME,
    'network': NETWORK_STACK_NAME,
    'core': CORE_STACK_NAME,
    'dns': DNS_STACK_NAME,
    'cluster': CLUSTER_STACK_NAME
}
