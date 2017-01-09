import os

import boto3
from cliff import show


class MadcoreBase(object):
    @classmethod
    def get_stack(cls, stack_name):
        cf = boto3.client('cloudformation')
        r = cf.describe_stacks(
            StackName=stack_name
        )
        return r['Stacks'][0]

    @property
    def config_path(self):
        cfg_path = os.path.join(os.path.expanduser("~"), '.madcore')

        return cfg_path


class ShowOne(show.ShowOne, MadcoreBase):
    pass
