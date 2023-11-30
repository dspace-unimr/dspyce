from .DSpaceObject import DSpaceObject
from .Item import Item
from .Collection import Collection
from .Community import Community
from .Relation import Relation


def item_from_dict(item_dict: dict):
    uuid = item_dict['uuid'] if 'uuid' in item_dict.keys() else ''
    handle = item_dict['handle'] if 'handle' in item_dict.keys() else ''
    collection = item_dict['collection'] if 'collection' in item_dict.keys() else ''
    item = Item(uuid, handle, collection)
    for m in filter(lambda x: x not in ('uuid', 'handle'), item_dict.keys()):
        field = m.split('.')
        if len(field) == 2:
            prefix = field[0]
            element = field[1]
            qualifier = None
        elif len(field) == 3:
            prefix = field[0]
            element = field[1]
            qualifier = field[2]
        else:
            raise KeyError(f'Could not parse metadata field label "{m}"')
        item.add_metadata(prefix, element, qualifier, item_dict[m])
    return item
