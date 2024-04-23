import re
import logging

import dspyce.entities
import dspyce.saf
import dspyce.rest
import dspyce.statistics
from dspyce.DSpaceObject import DSpaceObject
from dspyce.Item import Item
from dspyce.Collection import Collection
from dspyce.Community import Community
from dspyce.Relation import Relation


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
        case _:
            raise TypeError('The obj_type parameter must be one of (item, collection, community or None)'
                            f'but got {obj_type}')
    for key in filter(lambda x: re.search(r'[a-zA-Z0-9\-]\.[a-zA-Z0-9\-](\.[a-zA-Z0-9\-])?', x),
                      obj_dict.keys()):
        if not isinstance(obj_dict[key], list) and not isinstance(obj_dict[key], dict):
            obj.add_metadata(tag=key, value=obj_dict[key])
        elif isinstance(obj_dict[key], list):
            for o in obj_dict[key]:
                if isinstance(o, dict) and 'value' in o.keys():
                    obj.add_metadata(tag=key, value=o['value'],
                                     language=o['language'] if 'language' in o.keys() else None)
                else:
                    obj.add_metadata(tag=key, value=o)
        else:
            val = obj_dict[key]
            obj.add_metadata(tag=key, value=val['value'], language=val['language'] if 'language' in val.keys() else None)
    return obj
