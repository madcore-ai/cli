from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from base import CloudFormationBase
from const import STACK_DNS, ENDPOINTS


class CoreEndpoints(CloudFormationBase, Lister):
    def take_action(self, parsed_args):
        dns_stack = self.get_stack(STACK_DNS)

        domain_name = self.get_param_from_dict(dns_stack['Parameters'], 'DomainName')
        sub_domain_name = self.get_param_from_dict(dns_stack['Parameters'], 'SubDomainName')

        data = []

        for endpoint in ENDPOINTS.keys():
            data.append((endpoint, 'https://{}.{}.{}'.format(endpoint, sub_domain_name, domain_name)))

        return (
            ('Endpoint', 'Url'),
            data
        )
