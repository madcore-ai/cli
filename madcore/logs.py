import logging.config
import os

from madcore import utils

utils.create_project_config_dir()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'no_formatter': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(utils.project_logs_path(), 'madcore.log'),
            'formatter': 'standard'
        },
        'file_no_formatter': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(utils.project_logs_path(), 'madcore.log'),
            'formatter': 'no_formatter'
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(utils.project_logs_path(), 'madcore_error.log'),
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard'
        },
        'console_no_formatter': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'no_formatter'
        }
    },
    'loggers': {
        'no_formatter': {
            'handlers': ['console_no_formatter'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'file_no_formatter': {
            'handlers': ['console_no_formatter', 'file_no_formatter'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'file', 'file_error'],
            'level': 'DEBUG',
            'propagate': True,
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


def config_logs():
    logging.config.dictConfig(LOGGING)
