from .DSpaceObject import DSpaceObject
from .Item import Item
from .Collection import Collection
from .Community import Community
from .Relation import Relation
import saf


def item_from_dict(item_dict: dict, parse_lists: bool = True) -> Item:
    """
    Creates a DSpace Item based on a given dict. The keys must correspond exactly to the metadata fields.

    :param item_dict: The dict to create the item from.
    :param parse_lists: Checks if string values should be parsed as list, if written in the same schema.
    :return: The item as an Item object.
    """
    def is_list(p: str) -> list | None:
        """
        Small function to determine, if a string ist writen in a list format.

        :param p: The string to search through.
        :return: List, if list format is found else None
        """
        if len(p) == 0 or p[0] != '[' or p[-1] != ']':
            return None
        p = p[1:-1]
        lst = p.split(', ')
        if len(lst) == 1:
            return None
        return list(map(lambda x: x.strip("'").strip('"'), lst))

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
        if parse_lists and type(item_dict[m]) is str:
            tmp = is_list(item_dict[m])
            value = item_dict[m] if tmp is None else tmp
        else:
            value = item_dict[m]
        item.add_metadata(prefix, element, qualifier, value)
    return item
