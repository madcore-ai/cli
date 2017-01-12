import logging.config
import os

import utils

logs_path = os.path.join(utils.config_path(), 'logs')
if not os.path.exists(logs_path):
    os.makedirs(logs_path)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'output_tables': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(logs_path, 'madcore.log'),
            'formatter': 'standard'
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(logs_path, 'madcore_error.log'),
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard'
        },
        'console_table': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'output_tables'
        }
    },
    'loggers': {
        'output_table': {
            'handlers': ['console_table'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'file', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # disable this logs for now
        'boto3': {
            'level': 'CRITICAL',
        },
        'botocore': {
            'level': 'CRITICAL',
        },
        'nose': {
            'level': 'CRITICAL',
        },
        'stevedore.extension': {
            'level': 'CRITICAL',
        },
        'cliff.commandmanager': {
            'level': 'CRITICAL',
        },
        'requests': {
            'level': 'CRITICAL',
        },
        'urllib3': {
            'level': 'CRITICAL',
        }
    }
}

logging.config.dictConfig(LOGGING)
