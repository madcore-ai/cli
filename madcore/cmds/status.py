from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from madcore.base import MadcoreBase
from madcore.configs import config
from madcore.const import REPO_CLONE


class Status(MadcoreBase, Lister):
    _description = "Madcore status"

    def get_version(self, version):
        version = version if version.startswith('v') else ''
        return version

    def take_action(self, parsed_args):
        data = []

        headers = ('Repo', 'Branch', 'Local Version', 'Remote Version', 'Commit')

        for repo_name in REPO_CLONE:
            repo_config = config.get_repo_config(repo_name)
            version = repo_config.get('version', '')
            latest_version = repo_config.get('latest_version', '')

            data.append(
                (
                    repo_name,
                    repo_config.get('branch', ''),
                    self.get_version(version),
                    self.get_version(latest_version),
                    repo_config.get('commit', ''),
                )
            )

        return (
            headers,
            data
        )
