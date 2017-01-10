import os


def config_path():
    return os.path.join(os.path.expanduser("~"), '.madcore')


def setting_file_path():
    return os.path.join(config_path(), 'settings.json')
