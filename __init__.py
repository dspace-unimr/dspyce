import re

from .DSpaceObject import DSpaceObject
from .Item import Item
from .Collection import Collection
from .Community import Community
from .saf import *
from .rest import *


def from_dict(obj_dict: dict, obj_type: str = None) -> DSpaceObject | Item | Community | Collection:
    """
    Creates a new DSpaceObject from a given dictionary.
    Example for dict:
        {
          'uuid': <uuid>,

          'handle': <handle>,

          'name': <name>,

          '<dc.[...]>': <value>,

          '<[metadata-tag]>': <value> | list[<value>] | dict[lang: list[<value>]], # A list of metadata tags.

          'relation.<relation-name>': <uuid>, # A number of relationships with the connected uuids for items.

          'parent_community': <uuid>, # for possible parent communities if the obj_type is collection or community

          'collection': <uuid>, # A owning collection if the object is an Item.
        }

    >>> from_dict({'uuid': 'lkj-123-123-jlkjld', 'name': 'example',}, 'item')
    DSpaceObject('lkj-123-123-jlkjld', name='item')

    :param obj_dict: The dictionary containing the object information.
    :param obj_type: The type of DspaceObject. Must be one of (community, item, collection).
    :return: A DSpaceObject.
    """
    obj = None
    match obj_type:
        case None:
            obj = DSpaceObject(obj_dict['uuid'] if 'uuid' in obj_dict.keys() else '',
                               obj_dict['handle'] if 'handle' in obj_dict.keys() else '',
                               obj_dict['name'] if 'name' in obj_dict.keys() else '')
        case 'item':
            obj = Item(obj_dict['uuid'] if 'uuid' in obj_dict.keys() else '',
                       obj_dict['handle'] if 'handle' in obj_dict.keys() else '',
                       obj_dict['name'] if 'name' in obj_dict.keys() else '')
            if 'collection' in obj_dict.keys():
                obj.collections = [Collection(obj_dict['collection'])]
            relationships = filter(lambda x: re.search(r'^relation.', x), obj_dict.keys())
            for r in relationships:
                obj.add_relation(r.split('.')[1], obj_dict[r])

        case 'community':
            obj = Community(obj_dict['uuid'] if 'uuid' in obj_dict.keys() else '',
                            obj_dict['handle'] if 'handle' in obj_dict.keys() else '',
                            obj_dict['name'] if 'name' in obj_dict.keys() else '')
            if 'parent_community' in obj_dict.keys():
                obj.parent_community = Community(obj_dict['parent_community'])
        case 'collection':
            obj = Collection(obj_dict['uuid'] if 'uuid' in obj_dict.keys() else '',
                             obj_dict['handle'] if 'handle' in obj_dict.keys() else '',
                             obj_dict['name'] if 'name' in obj_dict.keys() else '')
            if 'parent_community' in obj_dict.keys():
                obj.parent_community = Community(obj_dict['parent_community'])
    for key in filter(lambda x: re.search(r'[a-zA-Z0-9\-]\.[a-zA-Z0-9\-](\.[a-zA-Z0-9\-])?', x),
                      obj_dict.keys()):
        tag = key.split('.')
        schema, element, qualifier = parse_metadata_label(tag)
        if type(obj_dict[key]) is not list and type(obj_dict[key]) is not dict:
            obj.add_metadata(schema, element, qualifier, value=obj_dict[key])
        elif type(obj_dict[key]) is list:
            for o in obj_dict[key]:
                obj.add_metadata(schema, element, qualifier, value=o)
        else:
            val = obj_dict[key]
            for lang in val.keys():
                obj.add_metadata(schema, element, qualifier, value=val[''], language=lang if lang != '' else None)
    return obj
