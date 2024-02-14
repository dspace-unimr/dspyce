import unittest
from dspyce.statistics.retrieve import get_point_views


class StatisticTest(unittest.TestCase):
    """
    Tests for statistics package.
    """
    def test_get_point_views(self):
        """
        Tests get_point_views function from statistics package.
        """
        self.assertEqual(get_point_views(
            {
                "id": "8ad84c46-bdf1-4558-9b90-5c43ff396980",
                "label": "Journals",
                "values": {
                    "views": 151
                },
                "type": "collection"
            }), 151)
        self.assertIsNone(get_point_views({"id": "8ad84c46-bdf1-4558-9b90-5c43ff396980", "label": "Journals"}))
        self.assertRaises(TypeError, get_point_views, 'Test')


if __name__ == '__main__':
    unittest.main()
