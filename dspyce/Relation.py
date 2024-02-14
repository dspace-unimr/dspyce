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
from dspyce import Item


class Relation:
    """
        The class Relation represents the relation between different DSPACE-entities. It stores the relation-type
        (relation_key) and id of the related Item.
    """
    relation_key: str
    relation_type: int
    items: tuple[Item, Item]

    def __init__(self, relation_key: str, related_items: tuple[Item, Item] = None, relation_type: int = None):
        """
            Creates a new object of the class relation, which represents exactly
            one DSpace-Relation

            :param relation_key: The relation-type, aka the name.
            :param related_items: The two related entities. Attention: The order will always be preserved.
            :param relation_type: A DSpace specific relation ID if existing.
        """
        self.relation_key = relation_key
        self.items = related_items if related_items is not None else (None, None)
        self.relation_type = relation_type

    def __str__(self):
        id_1 = self.items[0].get_identifier() if self.items[0] is not None else 'None'
        id_2 = self.items[1].get_identifier() if self.items[1] is not None else 'None'
        return f'{id_1}:relation.{self.relation_key}:{id_2}'

    def __eq__(self, other):
        return self.relation_key == other.relation_key and self.relation_type == other.relation_type

    def set_relation_type(self, relation_type: int):
        """
        Set a value for the relation_type variable.
        :param relation_type: The new relation_id value.
        """
        self.relation_type = relation_type
