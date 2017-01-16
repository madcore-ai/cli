from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from madcore.configs import config
from madcore.const import ENDPOINTS


class Endpoints(Lister):
    def take_action(self, parsed_args):
        user_config = config.get_user_data()

        data = []

        for endpoint in ENDPOINTS:
            data.append((endpoint, 'https://{}.{sub_domain}.{domain}'.format(endpoint, **user_config)))

        return (
            ('Endpoint', 'Url'),
            data
        )
