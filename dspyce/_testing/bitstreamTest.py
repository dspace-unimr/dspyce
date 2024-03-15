import unittest
from dspyce.bitstreams import Bundle
from dspyce.bitstreams import Bitstream


class BitstreamsTest(unittest.TestCase):
    bundle: Bundle = Bundle()
    bitstream: Bitstream = Bitstream('other', 'test-file')

    def test_init_bundle(self):
        self.assertIsInstance(self.bundle, Bundle)
        self.assertEqual(Bundle.DEFAULT_BUNDLE, self.bundle.name)

    def test_init_bitstream(self):
        self.assertIsInstance(self.bitstream, Bitstream)
        self.assertEqual('other', self.bitstream.file_name)

    def test_bundle_bitstream(self):
        self.bundle.add_bitstream(self.bitstream)
        self.assertIn(self.bitstream, self.bundle.get_bitstreams())
        self.bundle.remove_bitstream(self.bitstream)
        self.assertNotIn(self.bitstream, self.bundle.get_bitstreams())
