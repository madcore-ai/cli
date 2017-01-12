from __future__ import print_function

from madcore.cmds.registration import Registration
from madcore.logs import logging


class Configure(Registration):
    _description = "Config project with all external dependencies"

    log = logging.getLogger(__name__)
