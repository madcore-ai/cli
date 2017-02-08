from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from madcore.base import RepoBase
from madcore.const import REPO_CLONE


class Status(RepoBase, Lister):
    _description = "Madcore status"

    def take_action(self, parsed_args):
        data = []

        headers = ('Repo', 'Current Branch', 'Current Version', 'Current Commit', 'Latest Branch', 'Latest Version',
                   'Latest Commit')

        for repo_name in REPO_CLONE:
            info = self.get_repo_info(repo_name)

            data.append(
                (
                    repo_name,
                    info['local_branch'],
                    info['local_version'],
                    info['local_commit'],
                    info['remote_branch'],
                    info['remote_version'],
                    info['remote_commit'],
                )
            )

        return (
            headers,
            data
        )
