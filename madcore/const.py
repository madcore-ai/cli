from __future__ import unicode_literals

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
    'Email': 'polfilm@gmail.com',
    'OrganizationName': 'Madcore Ltd',
    'OrganizationalUnitName': 'Development',
    'LocalityName': 'London',
    'Country': 'GB'
}
