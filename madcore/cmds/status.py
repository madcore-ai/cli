from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from madcore.base import MadcoreBase
from madcore.configs import config
from madcore.const import REPO_CLONE


class Status(MadcoreBase, Lister):
    _description = "Madcore status"

    def take_action(self, parsed_args):
        data = []

        headers = ('Repo', 'Branch', 'Local Version', 'Commit', 'Remote Version')

        for repo_name in REPO_CLONE:
            repo_config = config.get_repo_config(repo_name)
            data.append(
                (
                    repo_name,
                    repo_config.get('branch', ''),
                    repo_config.get('version', ''),
                    repo_config.get('commit', ''),
                    'TODO',
                )
            )

        return (
            headers,
            data
        )
