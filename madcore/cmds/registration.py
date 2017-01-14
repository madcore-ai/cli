from __future__ import print_function, unicode_literals

from madcore.cmds.configure import Configure
import logging


class Registration(Configure):
    _description = "Register madcore"
    log = logging.getLogger(__name__)
