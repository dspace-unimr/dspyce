import unittest
from dspyce.bitstreams.models import Bundle
from dspyce.bitstreams.models import Bitstream


class BitstreamsTest(unittest.TestCase):
    bundle: Bundle = Bundle()
    bitstream: Bitstream = Bitstream('other', 'test-file', None, '123456789', True, 9876, 'md-123')

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

    def test_metadata(self):
        self.bitstream.add_metadata('dc.description', 'Hello World', 'en')
        self.assertEqual(self.bitstream.get_first_metadata_value('dc.description'), 'Hello World')
        self.assertEqual(self.bitstream.get_description(), 'Hello World')
        self.assertEqual(self.bitstream.get_metadata_values('dc.title')[0], 'other')
        self.assertEqual(self.bitstream.file_name, 'other')
        self.assertEqual(self.bitstream.get_dspace_object_type(), 'Bitstream')
        self.assertEqual(self.bitstream.size_bytes, 9876)
        self.assertEqual(self.bitstream.check_sum, 'md-123')
        self.assertTrue(self.bitstream.primary)

