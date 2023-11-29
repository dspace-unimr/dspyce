from Item import Item
# Relation.py
"""
This module contains the python class Relation representing the Relation between DSpace-Entities.
And the following function:
 - `export_relations(relations: list[Relation])` - Returns a list of relationships in a string.

Example:

    >from saf import export_relations
    >
    >export_relations([Relation('any_relation', '123456789/12'), Relation('different_relation', '123456789/13')])

    > relation.any_relation 123456789/12\nrelation.different_relation 123456789/13\n

"""


class Relation:
    """
        The class Relation represents the relation between different DSPACE-entities. It stores the relation-type
        (relation_key) and id of the related Item.
    """
    relation_key: str
    identifier: str
    item: Item

    def __init__(self, relation_key: str, related_identifier: str, related_item: Item = None):
        """
            Creates a new object of the class relation, which represents exactly
            one DSpace-Relation

            :param relation_key: The relation-type, aka the name.
            :param related_item: The handle/uuid/item-saf-id of the entity, to which the item is related.
        """
        self.relation_key = relation_key
        self.identifier = related_identifier
        self.item = related_item
        if (self.item is not None and (self.item.uuid == related_identifier or self.item.handle == related_identifier)
                and related_identifier != ''):
            raise ValueError('If a related Item object is provided, the related identifier must be empty or correspond'
                             'to this object.')
        elif self.item is not None and self.item.uuid != '':
            self.identifier = self.item.uuid

    def __str__(self):
        return "relation.{}:{}".format(self.relation_key, self.identifier)

    def __eq__(self, other):
        return self.relation_key == other.relation_key and self.identifier == other.identifier
