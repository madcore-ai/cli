from __future__ import print_function, unicode_literals

import logging
import os

from cliff.command import Command

from madcore import const
from madcore.base import RepoBase
from madcore.configs import config


class RepoConfigure(RepoBase, Command):
    logger = logging.getLogger(__name__)

    def get_remote_branches(self, repo_name, default_branch=None):
        exclude_branches = ['origin/HEAD -> origin/master']
        branches = []

        for branch in self.run_git_cmd('git branch -r', repo_name, debug=False).split('\n'):
            branch = branch.strip()
            if branch not in exclude_branches:
                branches.append(branch.split('/')[-1])

        if default_branch:
            branches.remove(default_branch)
            branches.insert(0, default_branch)

        return branches

    def check_if_commit_in_branch(self, repo_name, branch, commit):
        self.run_git_cmd('git checkout {branch} -q'.format(branch=branch), repo_name, debug=False)

        cmd = 'git branch -r --contains {commit}'.format(commit=commit)
        result = self.run_git_cmd(cmd, repo_name, debug=False)
        if result:
            branches = result.split('\n')
            for found_branch in branches:
                if branch in found_branch:
                    return True

        return False

    def ask_for_repo_inputs(self, repo_name, default_branch, default_commit):
        repo_config = config.get_repo_config(repo_name)

        default_branch = repo_config.get('branch', '') or default_branch
        commit = repo_config.get('commit', '') or default_commit

        last_error = ''

        while True:
            prompt = ''
            if last_error:
                prompt += last_error + '\n'
            if self.env in (const.ENVIRONMENT_DEV,):
                branches = self.get_remote_branches(repo_name, default_branch)
                branch_prompt = prompt + "[%s] Repo branch: " % repo_name
                sel_branch = self.single_prompt('branch', options=branches, prompt=branch_prompt)
                branch = sel_branch['branch']
            else:
                branch = self.env_branch

            latest_local_commit, latest_remote_commit = self.get_repo_last_commit(repo_name, branch)

            options = []

            if default_commit and branch == default_branch:
                options.append('current(%s)' % default_commit)

            if latest_remote_commit != latest_local_commit or branch != default_branch:
                options.append('latest(%s)' % latest_remote_commit)

            show_input_commit = False
            if options:
                options.append('custom(input custom commit id)')

                commit_prompt = prompt + "[%s][%s] Select commit: " % (repo_name, branch)

                sel_commit = self.single_prompt('commit', options=options, prompt=commit_prompt)

                if sel_commit['commit'].startswith('custom'):
                    show_input_commit = True
                elif sel_commit['commit'].startswith('latest'):
                    commit = latest_remote_commit
            else:
                show_input_commit = True

            if show_input_commit:
                commit_prompt = "[%s][%s] Input commit: " % (repo_name, default_branch)
                sel_commit = self.raw_prompt('commit', commit_prompt, default=latest_remote_commit,
                                             default_label='latest')
                commit = sel_commit['commit']

            if commit:
                if self.check_if_commit_in_branch(repo_name, branch, commit):
                    break
                else:
                    last_error = "[%s][%s] Commit not found: '%s'" % (repo_name, branch, commit)
                    self.logger.error(last_error)
            else:
                break

        return branch, commit

    def repo_reset_to_commit(self, repo_name, branch, commit):
        self.logger.info("[%s] Reset repos to version defined in config.", repo_name)
        self.run_git_cmd('git checkout {branch}'.format(branch=branch), repo_name)
        self.run_git_cmd('git fetch', repo_name)
        self.run_git_cmd('git --no-pager log -50 --pretty=oneline', repo_name, log_result=True)
        self.run_git_cmd('git reset --hard {commit}'.format(commit=commit), repo_name, log_result=True)

        self.logger.info("[%s] Last commit on branch '%s'.", repo_name, branch)
        self.run_git_cmd('git --no-pager log -1', repo_name, log_result=True)

    def repo_pull_latest_version(self, repo_name, branch):
        self.logger.info("[%s] Get latest version from branch '%s'.", repo_name, branch)
        self.run_git_cmd('git checkout {branch}'.format(branch=branch), repo_name, log_result=True)
        self.run_git_cmd('git reset --hard origin/{branch}'.format(branch=branch), repo_name, log_result=True)

        self.logger.info("[%s] Last commit on branch '%s'.", repo_name, branch)
        self.run_git_cmd('git --no-pager log -1', repo_name, log_result=True)

    def clone_repo(self, repo_name, parsed_args):
        self.log_figlet("Clone '%s'", repo_name)

        repo_url = os.path.join(const.REPO_MAIN_URL, '%s.git' % repo_name)
        repo_path = os.path.join(self.config_path, repo_name)

        repo_config = config.get_repo_config(repo_name)

        # default we use to clone from this branch and commit
        default_branch = self.env_branch
        default_commit = 'FETCH_HEAD'

        config_branch = repo_config.get('branch', '')
        config_commit = repo_config.get('commit', '')

        if not parsed_args.force:
            if self.env in (const.ENVIRONMENT_DEV,):
                branch = config_branch or default_branch
            else:
                branch = default_branch
            commit = config_commit
        else:
            branch = default_branch
            commit = default_commit

        self.clone_repo_latest_version(repo_name, branch)

        if not os.path.exists(repo_path):
            self.run_cmd('git clone -b %s %s' % (branch, repo_url), cwd=self.config_path, log_prefix=repo_name)
        else:
            self.logger.info("[%s] Repo already exists.", repo_name)

        if not parsed_args.force:
            if parsed_args.reset or (not config_branch and not config_commit):
                branch, commit = self.ask_for_repo_inputs(repo_name, branch, commit)
                config.set_repo_config(repo_name, {'branch': branch, 'commit': commit})

        if parsed_args.force:
            self.repo_pull_latest_version(repo_name, branch)
        elif commit:
            self.repo_reset_to_commit(repo_name, branch, commit)

    def take_action(self, parsed_args):
        self.log_figlet("Clone repos")

        self.logger.info("Start cloning all required repos.")

        for repo_name in const.REPO_CLONE:
            self.clone_repo(repo_name, parsed_args)

        self.logger.info("End cloning all required repos.")

        self.app.run_subcommand(['status'])
