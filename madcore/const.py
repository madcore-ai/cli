from __future__ import unicode_literals

AWS_IDENTITY_POOL_ID = 'eu-west-1:964ea940-a8e6-44a5-a88b-c510cfe487d7'

STACK_FOLLOWME = 'MADCORE-FollowMe'
STACK_S3 = 'MADCORE-S3'
STACK_NETWORK = 'MADCORE-Net'
STACK_CORE = 'MADCORE-Core'
STACK_CLUSTER = 'MADCORE-Cluster'
STACK_DNS = 'MADCORE-Dns'

# used to load parameters files
STACK_SHORT_NAMES = {
    'sgfm': STACK_FOLLOWME,
    's3': STACK_S3,
    'network': STACK_NETWORK,
    'core': STACK_CORE,
    'dns': STACK_DNS,
    'cluster': STACK_CLUSTER
}

# define all static endpoints
ENDPOINTS = {
    'influxdb': {},
    'jenkins': {},
    'kubeapi': {},
    'kubedash': {},
    'grafana': {},
    'spark': {},
    'zeppelin': {}
}

DOMAIN_REGISTRATION = {
    'Hostname': '',  # to be set dynamically
    'Email': '',  # user email
    'OrganizationName': 'Madcore Ltd',
    'OrganizationalUnitName': 'Development',
    'LocalityName': 'London',
    'Country': 'GB',
    'S3BucketName': '',
}

ALLOWED_INSTANCE_TYPES = [
    't2.small',
    'm3.medium',
    'm4.large',
    'r3.large'
]
