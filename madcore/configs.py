import ConfigParser
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

    def get_aws_data(self, key=None, section='aws'):
        return self.get_data(section, key)

    def get_login_data(self, key=None, section='login'):
        return self.get_data(section, key)

    def get_data(self, section, key=None):
        try:
            data = dict(self.config.items(section))
            if key:
                return data[key]
            return data
        except ConfigParser.Error:
            pass

        return {}

    def get_user_data(self, key=None, section='user'):
        return self.get_data(section, key)

    def get_full_domain(self):
        return '{sub_domain}.{domain}'.format(**self.get_user_data())

    def is_key_true(self, section, key):
        try:
            return self.config.getboolean(key, section)
        except ConfigParser.Error:
            pass

        return False

    @property
    def is_dns_delegated(self):
        return self.is_key_true('dns_delegation', 'user')

    @property
    def is_domain_registered(self):
        return self.is_key_true('registration', 'user')

    @property
    def is_config_deleted(self):
        return self.is_key_true('config_deleted', 'user')

    @property
    def is_user_created(self):
        try:
            created = self.config.getboolean('user', 'created')
            verified = self.config.getboolean('user', 'verified')

            return all((created, verified))
        except ConfigParser.Error:
            pass

        return False

    @property
    def is_logged_in(self):
        return self.is_key_true('login', 'login')


config = MadcoreConfig()
