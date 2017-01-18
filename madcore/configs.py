from __future__ import unicode_literals, print_function

import ConfigParser
import json
import os

from madcore import utils


class MadcoreConfig(object):
    def __init__(self):
        self.config_file_path = utils.config_file_path()
        self.config = ConfigParser.SafeConfigParser()

        self._load_config()

    def _load_config(self):
        # only load config if project config path is present
        if os.path.exists(utils.project_config_dir()):
            if os.path.exists(self.config_file_path):
                self.config.read(self.config_file_path)
            else:
                with open(self.config_file_path, 'wb') as configfile:
                    configfile.write('')

    def save_config(self):
        with open(self.config_file_path, 'wb') as configfile:
            self.config.write(configfile)

    def add_section_if_not_exists(self, section):
        if not self.config.has_section(section):
            self.config.add_section(section)

    def get_aws_identity_id(self, section='aws'):
        try:
            return self.config.get(section, 'identity_id')
        except ConfigParser.Error:
            pass

        return None

    def set_aws_identity_id(self, identity_id):
        self.set_aws_data({'identity_id': identity_id})

    def set_data(self, data, section):
        self.add_section_if_not_exists(section)
        for key, val in data.items():
            if isinstance(val, bool):
                val = str(val).lower()
            elif isinstance(val, (int, float)):
                val = str(val)
            self.config.set(section, key, val)

        self.save_config()

    def set_user_data(self, user_data, section='user'):
        self.set_data(user_data, section)

    def set_login_data(self, login_data, section='login'):
        self.set_data(login_data, section)

    def set_aws_data(self, aws_data, section='aws'):
        self.set_data(aws_data, section)

    def set_plugin_installed(self, plugin_name, default=True):
        self.set_data({"installed": default}, section=plugin_name)

    def set_plugin_deleted(self, plugin_name, default=True):
        self.set_data({"installed": not default}, section=plugin_name)

    def set_plugin_job_params(self, plugin_name, job_name, params):
        self.set_data({job_name: json.dumps(params)}, section=plugin_name)

    def delete_plugin_job_params(self, plugin_name, job_names):
        if not isinstance(job_names, list):
            job_names = [job_names]

        for job_name in job_names:
            try:
                self.config.remove_option(plugin_name, job_name)
            except:
                pass

    def get_plugin_job_params(self, plugin_name, job_name):
        params = self.get_data(plugin_name, job_name)
        if params:
            params = json.loads(params)

        return params or None

    def get_aws_data(self, key=None, section='aws'):
        return self.get_data(section, key)

    def get_login_data(self, key=None, section='login'):
        return self.get_data(section, key)

    def get_data(self, section, key=None):
        try:
            data = dict(self.config.items(section))
            if key:
                return data.get(key, None)
            return data
        except ConfigParser.Error:
            pass

        return {}

    def get_user_data(self, key=None, section='user'):
        return self.get_data(section, key)

    def get_full_domain(self):
        return '{sub_domain}.{domain}'.format(**self.get_user_data())

    def is_key_true(self, key, section):
        try:
            return self.config.getboolean(section, key)
        except ConfigParser.Error:
            pass

        return False

    @property
    def is_config_deleted(self):
        return self.is_key_true('config_deleted', 'user')

    def is_plugin_installed(self, plugin_name):
        return self.is_key_true('installed', plugin_name)


config = MadcoreConfig()
