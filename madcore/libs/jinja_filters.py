from __future__ import unicode_literals, print_function

import logging

from madcore.const import EC2_SPOT_PRICE_ADD_EXTRA
from madcore.libs.jinja import ENV

logger = logging.getLogger(__name__)


def spot_price(instance_type, add_extra=None, verbose=False):
    # import here to avoid circular import
    # TODO@geo fix this
    from madcore.base import AwsBase
    spot_price_history = AwsBase().get_instance_spot_price_history(instance_type)

    if spot_price_history:
        latest_spot_price = spot_price_history[0]['SpotPrice']
    else:
        # TODO@geo What we do if there is no price for specific instance type?
        latest_spot_price = 0
        logger.debug("No spot price history found for instance type: '%s'", instance_type)

    if add_extra is None:
        add_extra = EC2_SPOT_PRICE_ADD_EXTRA.get(instance_type, 0.0050)

    if verbose:
        result = ' + '.join((str(latest_spot_price), str(add_extra)))
    else:
        result = float(latest_spot_price) + float(add_extra)

    return result


# register all custom filters here
ENV.filters['spot_price'] = spot_price
