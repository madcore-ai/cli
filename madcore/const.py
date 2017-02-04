from __future__ import unicode_literals

AWS_IDENTITY_POOL_ID = 'eu-west-1:964ea940-a8e6-44a5-a88b-c510cfe487d7'

STACK_FOLLOWME = 'MADCORE-FollowMe'
STACK_S3 = 'MADCORE-S3'
STACK_NETWORK = 'MADCORE-Net'
STACK_CORE = 'MADCORE-Core'
STACK_CLUSTER = 'MADCORE-Cluster'
STACK_DNS = 'MADCORE-Dns'

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

EC2_SPOT_PRICE_ADD_EXTRA = {
    'm3.medium': 0.0050,
    'm4.large': 0.0050,
    'r3.large': 0.0050
}

PLUGIN_CLOUDFORMATION_JOB_TYPE = 'cloudformations'
PLUGIN_JENKINS_JOB_TYPE = 'jobs'

PLUGIN_TYPE_CLUSTER = 'cluster'
PLUGIN_TYPE_PLUGIN = 'plugin'

ENVIRONMENT_PROD = 'prod'
ENVIRONMENT_DEV = 'dev'

ENVIRONMENT_BRANCH = {
    'prod': 'master',
    'dev': 'development'
}

REPO_MAIN_URL = 'https://github.com/madcore-ai'
REPO_CLONE = [
    'core',
    'plugins',
    'cloudformation',
    'containers'
]
