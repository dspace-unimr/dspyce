import unittest

from dspyce._testing.dspyceTest import DSpaceObjectTest
from dspyce._testing.statisticsTest import StatisticTest
from dspyce._testing.metadataTests import MetadataTest
from dspyce._testing.itemTests import ItemTest
from dspyce._testing.relationTest import RelationTest
from dspyce._testing.bitstreamTest import BitstreamsTest
from dspyce._testing.safTest import SAFTest


class InitTests(unittest.TestCase):
    """Dummy test class"""
    pass


if __name__ == '__main__':
    unittest.main()
