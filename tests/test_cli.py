from madcore.cli import MadcoreCli
from tests import MadcoreTestCase
import logging


class TestMadcoreCli(MadcoreTestCase):
    def test_init(self):
        logging.disable(logging.NOTSET)
        MadcoreCli(load_plugins=False)
