# saf/Relation.py
"""
This module contains the python class Relation representing the Relation between DSpace-Entities.
And the following function:
 - `export_relations(relations: list)` - Returns a list of relationships in a string.

Example:
        > from saf.Relation import export_relations

        > export_relations([Relation('any_relation', '123456789/12'), Relation('different_relation', '123456789/13')])

        relation.any_relation 123456789/12
        relation.different_relation 123456789/13\n
"""


class Relation:
    """
        Die Klasse Relation repräsentiert Beziehungen zwischen unterschiedlichen
        DSPACE-Entitäten. Sie speichert Beziehungstyp (relation_key), und handle.
    """
    relation_key: str
    handle: str

    def __init__(self, relation_key: str, handle: str):
        """
            Erstellt ein neues Objekt der Klasse Relation, welches genau eine
            Beziehung repräsentiert.

            :param relation_key: Der Beziehungstyp, bzw. die Bezeichnung.
            :param handle: Der Handle, der Entität zu der die Beziehung beschreiben wird.
        """
        self.relation_key = relation_key
        self.handle = handle

    def __str__(self):
        return "relation.{} {}".format(self.relation_key, self.handle)

    def __add__(self, other):
        return str(self) + '\n' + str(other)


def export_relations(relations: list[Relation]) -> str:
    """
        Erhält eine Liste von Relations und gibt den Inhalt der Export-Datei
        relationships zurück.

        :param relations: Eine Liste mit Objekten der Klasse "Relation"
        :return: Den Inhalt der Datei "relationships" als string.
    """
    rel_txt = ""
    for r in relations:
        rel_txt += str(r) + '\n'
    return rel_txt
