import os
import socket
import time

import pkg_resources


def project_config_dir():
    return os.path.join(os.path.expanduser("~"), '.madcore')


def config_file_path():
    return os.path.join(project_config_dir(), 'config')


def project_logs_path():
    return os.path.join(project_config_dir(), 'logs')


def create_project_config_dir():
    cfg_path = project_config_dir()

    if not os.path.exists(cfg_path):
        os.makedirs(cfg_path)

    logs_path = project_logs_path()
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)


def hostname_resolves(hostname, max_time=700):
    sleep_time = 3
    count = 0

    while True:
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.error:
            time.sleep(sleep_time)
            count += sleep_time
            if count > max_time:
                break


def get_version():
    dist = pkg_resources.get_distribution("madcore")
    return dist.version
