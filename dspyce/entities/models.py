# entities/models.py
"""
Python package for analysing and working with entity modells in DSpace.
This module contains the EntityModell class and three functions to work with entities. You can create a new EntityModell
object based on the relationship-types.xml file or a given REST-endpoint and you can check whether a given endpoint
has an entity modell enabled or not.
"""
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import networkx as nx
from dspyce.rest import RestAPI


class EntityModell:
    """
    The EntityModell class provides methods and attributes to work with entity modells. An object of this class
    represents entities and relationships of a DSpace repository.
    """

    entities: list[str]
    """A list of existing entities."""
    relations: list[str]
    """A list of the names of existing relations."""
    entity_model: nx.Graph
    """The networkx graph representing the entity model."""

    def __init__(self):
        """
        Creates a new object of the entity model.
        """
        self.entities = []
        self.relations = []
        self.entity_modell = nx.MultiDiGraph()

    def has_entity(self, entity: str) -> bool:
        """
        Checks if the current entity already exits.

        :param entity: The name of the entity to check for.
        :return: True if the entity exists already in the entity model.
        """
        return entity in self.entities

    def has_relation(self, relation: str) -> bool:
        """
        Checks if the current relation already exits.

        :param relation: The name of the relation to check for.
        :return: True if the relation exists already in the entity model.
        """
        return relation in self.relations

    def add_entity(self, entity: str):
        """
        Adds a new entity to the entity modell.

        :param entity: The name of the entity to add to the modell.
        :raises AttributeError: If the entity already exists.
        """
        if not self.has_entity(entity):
            self.entities.append(entity)
            self.entity_modell.add_node(entity)
        else:
            raise ValueError(f"The entity {entity} already exists.")

    def add_relation(self, from_entity: str, to_entity: str, relation_name: str):
        """
        Adds a relation between two entities. Relations are always directional.

        :param from_entity: The name of the starting entity.
        :param to_entity: The name of the target entity.
        :param relation_name: The name of the relation between the two entities.
        :raises AttributeError: If the relation already exists.
        """
        if not self.has_relation(relation_name):
            self.entity_modell.add_edge(from_entity,
                                        to_entity,
                                        label=relation_name)
        else:
            raise ValueError(f"The relation {relation_name} already exists.")

    def draw_graph(self, show: bool = True, path: str = None):
        """
        Draws the current entity model as a graph using matplotlib.

        :param show: If true the graph will be displayed in a plt figure.
        :param path: The path and file_name where the graph should be saved. If None, the graph won't be saved.
        """
        plt.axis('off')
        fig, ax = plt.subplots(figsize=(2.13*len(self.entities)+2,
                                        1.6*len(self.entities)+2))
        ax.axis('off')
        pos = nx.spring_layout(self.entity_modell, scale=2)
        # con_style = 'arc3, rad=0.1'
        con_style = [f"arc3,rad={r}" for r in [0.2, 0.6, 0.9, 1.2]]
        nx.draw_networkx(self.entity_modell, pos,
                         node_size=1500, alpha=0.9, node_shape='s',
                         edge_color='grey', connectionstyle=con_style,
                         min_source_margin=30, min_target_margin=30, label='labels',
                         verticalalignment='center_baseline',
                         font_color='black', bbox={"alpha": 0.7, "color": "white"}, ax=ax
                         )
        nx.draw_networkx_edge_labels(
            self.entity_modell, pos, nx.get_edge_attributes(self.entity_modell, 'label'),
            label_pos=0.5, font_color='black', bbox={"alpha": 0.9, "color": "white"},
            connectionstyle=con_style, ax=ax)
        if path is not None:
            fig.savefig(path)
        if show:
            fig.show()

    def get_relation_list(self) -> list[tuple[tuple[str, str], str]]:
        """
        Returns a list of all relations and the connected entity types.

        :return: Returns the list in the following format [((left_type, right_type), relation_name), ...]
        """
        return [((l, r), attr['label']) for l, r, attr in self.entity_modell.edges(data=True)]


def from_relationship_file(path: str) -> EntityModell:
    """
    Loads a EntityModell from a given DSpace relationship file, aka `relationship-types.xml`.

    :param path: The path to the relationship xml file.
    :return: A complete EntityModell object based on the content provided from the relationship file.
    """
    with open(path, 'r', encoding='utf8') as f:
        bs = BeautifulSoup(f.read(), 'xml')
    relationships = bs.relationships
    md = EntityModell()
    for r in relationships.contents:
        if r.name == 'type':
            left_type = r.leftType.string
            right_type = r.rightType.string
            if not md.has_entity(left_type):
                md.add_entity(left_type)
            if not md.has_entity(right_type):
                md.add_entity(right_type)
            md.add_relation(right_type, left_type, r.leftwardType.string)
            md.add_relation(left_type, right_type, r.rightwardType.string)
    return md


def from_rest_api(url: str) -> EntityModell:
    """
    Creates an EntityModell object based on the information provided from the REST API

    :param url: The url of the used RestApi.
    :return: A complete EntityModell object based on the RestAPI provided.
    """
    rest = RestAPI(url)
    entity_objects = rest.get_paginated_objects('core/entitytypes', 'entitytypes')
    entity_objects = list(filter(lambda x: x['label'] != 'none', entity_objects))
    if len(entity_objects) == 0:
        raise ValueError(f'No entity types found in instance "{url}"')
    em = EntityModell()
    [em.add_entity(e['label']) for e in entity_objects]
    relations = rest.get_paginated_objects('core/relationshiptypes', 'relationshiptypes')
    for r in relations:
        leftward_type = r['leftwardType']
        rightward_type = r['rightwardType']
        left_type = rest.get_api(f'core/entitytypes/{r["_links"]["leftType"]["href"].split("/")[-1]}')['label']
        right_type = rest.get_api(f'core/entitytypes/{r["_links"]["rightType"]["href"].split("/")[-1]}')['label']
        if not em.has_relation(leftward_type):
            em.add_relation(right_type, left_type, leftward_type)
        if not em.has_relation(rightward_type):
            em.add_relation(left_type, right_type, rightward_type)
    return em


def check_entities_rest(url: str) -> bool:
    """
    Checks if the given rest endpoint has entities enabled.

    :param url: The url of the rest-API
    """
    entity_objects = RestAPI(url).get_paginated_objects('core/entitytypes', 'entitytypes')
    return len(list(filter(lambda x: x['label'] != 'none', entity_objects))) > 0
