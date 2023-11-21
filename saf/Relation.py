# saf/Relation.py
"""
This module contains the python class Relation representing the Relation between DSpace-Entities.
And the following function:
 - `export_relations(relations: list)` - Returns a list of relationships in a string.

Example:

    >from saf.Relation import export_relations
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
    handle: str

    def __init__(self, relation_key: str, related_item: str):
        """
            Creates a new object of the class relation, which represents exactly
            one DSpace-Relation

            :param relation_key: The relation-type, aka the name.
            :param related_item: The handle/uuid/item-saf-id of the entity, to which the item is related.
        """
        self.relation_key = relation_key
        self.handle = related_item

    def __str__(self):
        return "relation.{} {}".format(self.relation_key, self.handle)

    def __add__(self, other):
        return str(self) + '\n' + str(other)


def export_relations(relations: list[Relation]) -> str:
    """
        Creates a list of relationships separated by line-breaks. It can be used to create the relationship-file in a
        saf-package.

        :param relations: A list of objects of the class "Relation"
        :return: The line-break separated list of relationships as a string.
    """
    return '\n'.join([str(r) for r in relations])
