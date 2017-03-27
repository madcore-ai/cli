from __future__ import unicode_literals, print_function

import logging
import os
import pprint
import sys
from collections import OrderedDict

import yaml
from cerberus import Validator

from madcore import const
from madcore.libs.validators import VALIDATORS
from madcore.utils import project_config_dir

logger = logging.getLogger(__name__)

PARAMETERS_VALIDATION_SCHEMA = {
    "type": "list",
    "required": False,
    "schema": {
        "type": "dict",
        "schema": {
            "name": {
                "type": "string",
                "empty": False,
            },
            "value": {
                "anyof_type": ['string', 'integer'],
                "empty": True,
                "nullable": True
            },
            "default_label": {
                "type": "string",
                "required": False,
                "empty": True,
            },
            "description": {
                "type": "string",
                "empty": True,
            },
            "type": {
                "type": "string",
                "empty": False,
                "allowed": VALIDATORS.keys(),
            },
            "allowed": {
                "type": "list",
                "required": False,
                "schema": {
                    "anyof_type": ['string', 'integer', 'boolean'],
                }
            },
            "prompt": {
                "type": "boolean",
                "required": False
            },
            "cache": {
                "type": "boolean",
                "required": False
            }
        }
    }
}

PLUGIN_VALIDATION_SCHEMA = {
    "id": {
        "type": "string",
        "empty": False
    },
    "type": {
        "type": "string",
        "empty": False,
        "allowed": [const.PLUGIN_TYPE_PLUGIN, const.PLUGIN_TYPE_CLUSTER],
    },
    "image": {
        "type": "string",
        "empty": True
    },
    "description": {
        "type": "string",
        "empty": False
    },
    "bullets": {
        "type": "list",
        "empty": True,
        "schema": {
            "type": "string"
        }
    },
    "text_active": {
        "type": "string",
        "empty": False
    },
    "text_buy": {
        "type": "string",
        "empty": False
    },
    "text_inactive": {
        "type": "string",
        "empty": False
    },
    "text_prerequesite": {
        "type": "string",
        "empty": False
    },
    "frame_color": {
        "type": "string",
        "empty": False
    },
    "parameters": PARAMETERS_VALIDATION_SCHEMA,
    "cloudformations": {
        "type": "list",
        "required": False,
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "empty": False
                },
                "stack_name": {
                    "type": "string",
                    "empty": False
                },
                "template_file": {
                    "type": "string",
                    "empty": False
                },
                "capabilities": {
                    "type": "list",
                    "required": False,
                    "schema": {
                        "type": "string"
                    }
                },
                "parameters": PARAMETERS_VALIDATION_SCHEMA
            }
        }
    },
    "jobs": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "empty": False
                },
                "private": {
                    "type": "boolean",
                    "required": False,
                },
                "sequence": {
                    "type": "list",
                    "required": False,
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "type": {
                                "type": "string",
                                "allowed": ["cloudformation", "job"],
                                "empty": False
                            },
                            "name": {
                                "type": "string",
                                "empty": False
                            },
                            "description": {
                                "type": "string",
                                "empty": False
                            },
                            "job_name": {
                                "type": "string",
                                "empty": False
                            },
                            "action": {
                                "type": "string",
                                "empty": False,
                                "allowed": ["create", "update", "delete", "status"],
                            },
                            "parameters": PARAMETERS_VALIDATION_SCHEMA
                        }
                    }
                },
                "parameters": PARAMETERS_VALIDATION_SCHEMA
            }
        }
    }
}


class MadcorePluginDefinition(object):
    def __init__(self, plugin_data):
        self._plugin_data = plugin_data
        self._jobs_data = {
            'jobs': OrderedDict(),
            'cloudformations': OrderedDict(),
        }
        self.validator = Validator(PLUGIN_VALIDATION_SCHEMA)

    @property
    def plugin_data(self):
        if isinstance(self._plugin_data, list):
            data = self._plugin_data[0]
        else:
            data = self._plugin_data

        return data

    @property
    def plugin_name(self):
        return self.plugin_data['id']

    @property
    def is_valid(self):
        return self.validator.validate(self.plugin_data)

    @property
    def validation_error(self):
        return self.validator.errors

    @property
    def plugin_level_parameters(self):
        return self.plugin_data.get('parameters', [])

    @property
    def jobs_list(self):
        return self.plugin_data.get('jobs', [])

    @property
    def public_jobs_list(self):
        return [job for job in self.jobs_list if not job.get('private', False)]

    @property
    def cloudformations_list(self):
        return self.plugin_data.get('cloudformations', [])

    @property
    def jobs(self):
        if not self._jobs_data['jobs']:
            for job in self.jobs_list:
                self._jobs_data['jobs'][job['name']] = job
        return self._jobs_data['jobs']

    @property
    def cloudformations(self):
        if not self._jobs_data['cloudformations']:
            for job in self.cloudformations_list:
                self._jobs_data['cloudformations'][job['name']] = job
        return self._jobs_data['cloudformations']

    def get_jobs_by_type(self, job_type):
        return getattr(self, job_type, [])

    @property
    def is_cluster(self):
        return self.plugin_data['type'] in const.PLUGIN_TYPE_CLUSTER

    def __getitem__(self, item):
        return self.plugin_data.get(item, None)

    def __repr__(self):
        return "%s(name=%s)" % (self.__class__.__name__, self.plugin_name)


class PluginsLoader(object):
    def __init__(self, plugins_dir=None, load=False):
        self.plugins_dir = plugins_dir or project_config_dir('plugins')

        self._plugins = OrderedDict()

        if load:
            self.load()

    def check_plugins_dir_exists(self):
        if not os.path.exists(self.plugins_dir):
            logger.error("No 'plugins' repo found, you need to run configuration.")
            sys.exit(1)

    def load(self, check_exists=True):
        if check_exists:
            self.check_plugins_dir_exists()

        config_file_name = 'madcore.yaml'

        for plugin_name in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, plugin_name)
            # Skip any hidden dirs like .git
            if plugin_name.startswith('.') or os.path.isfile(plugin_path):
                continue

            plugin_config_path = os.path.join(plugin_path, config_file_name)

            if not os.path.exists(plugin_config_path):
                logger.error("[%s] Error loading plugin, %s config not found, skip.", plugin_name, config_file_name)
                continue

            with open(plugin_config_path, 'r') as plugin_file:
                try:
                    plugin = MadcorePluginDefinition(yaml.load(plugin_file))
                except Exception as e:
                    logger.error("[%s] Error loading %s, invalid file.", plugin_name, config_file_name)
                    logger.error(e)
                    continue
                if plugin.is_valid:
                    self._plugins[plugin.plugin_name] = plugin
                else:
                    logger.error("[%s] Validation errors:", plugin_name)
                    logger.error("[%s] %s", plugin_name, pprint.pformat(plugin.validation_error))

    @property
    def plugins(self):
        return self._plugins


# Some kind of singleton here
plugins_loader = PluginsLoader()
