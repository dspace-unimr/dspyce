import unittest

import dspyce as ds


class RelationTest(unittest.TestCase):
    """
    Tests methods from Relation class.
    """
    relation = ds.Relation('isAuthorOfPublication',
                           (ds.Item('abc'),
                            ds.Item('dfg')), 2)

    def test_str(self):
        """
        Tests __str__ method.
        """
        self.assertEqual('abc:relation.isAuthorOfPublication:dfg', str(self.relation))

    def test_eq(self):
        """
        Tests __eq__ method.
        """
        self.assertEqual(ds.Relation('isAuthorOfPublication', (ds.Item(), ds.Item()),
                                     2), self.relation)
        self.assertNotEqual(ds.Relation('isAuthorOfPublication', (ds.Item(), ds.Item())),
                            self.relation)

    def test_set_relation_type(self):
        """
        Tests set_relation_type method.
        """
        self.relation.set_relation_type(1)
        self.assertEqual(1, self.relation.relation_type)


if __name__ == '__main__':
    unittest.main()
