from .. import DSpaceObject, Item, Community, Collection
from ..DSpaceObject import parse_metadata_label


def json_to_object(json_content: dict) -> DSpaceObject | Item | Community | Collection | None:
    """
    Converts a dict based on REST-format in to a DSpace Object.

    :param json_content: The json content in a dict format.
    :return: A DSpaceObject object.
    """
    uuid = json_content['uuid']
    name = json_content['name']
    handle = json_content['handle']
    metadata = json_content['metadata']
    doc_type = json_content['type']
    # _links = {}
    # for link in json_content['_links'].keys():
    #    if type(json_content['_links'][link]) is dict and 'href' in json_content['_links'][link].keys():
    #        _links[link] = json_content['_links'][link]['href']
    #    elif type(json_content['_links'][link]) is list:
    #        _links[link] = {li['name']: li['href'] for li in json_content['_links'][link]}
    if json_content is None:
        return None
    match doc_type:
        case 'community':
            obj = Community(uuid, handle=handle, name=name)
        case 'collection':
            obj = Collection(uuid, handle=handle, name=name)
        case 'item':
            obj = Item(uuid, handle=handle, name=name)
        case _:
            obj = DSpaceObject(uuid, handle, name)
    for m in metadata.keys():
        prefix, element, qualifier = parse_metadata_label(m)
        for v in metadata[m]:
            value = v['value']
            lang = v['language'] if 'language' in v.keys() else None
            obj.add_metadata(prefix, element, qualifier, value, lang)
    return obj


def object_to_json(obj: DSpaceObject) -> dict:
    """
    Converts a DSpaceObject class into dict based on a DSpace-Rest format
    :param obj: The object to convert.
    :return: A dictionary in the REST-format.
    """
    uuid = obj.uuid
    handle = obj.handle
    name = obj.name
    obj_type = obj.get_dspace_object_type().lower()
    metadata = {}
    for m in obj.metadata:
        value = m.value if type(m.value) is list else [m.value]
        values = []
        for v in value:
            tmp = {'value': v}
            if m.language is not None and m.language != '':
                tmp['language'] = m.language
            values.append(tmp)
        metadata[m.get_tag()] = values if m.get_tag() not in metadata.keys() else metadata[m.get_tag()] + values

    json_object = {}
    if uuid is not None and uuid != '':
        json_object['uuid'] = uuid
    if handle is not None and handle != '':
        json_object['handle'] = handle
    if name is not None and name != '':
        json_object['name'] = name
    if obj_type is not None and obj_type != '':
        json_object['type'] = obj_type
    if type(obj) is Item:
        obj: Item
        json_object['inArchive'] = obj.in_archive
        json_object['discoverable'] = obj.discoverable
        json_object['withdrawn'] = obj.withdrawn
        if obj.is_entity():
            json_object['entityType'] = obj.metadata.get('dspace.entity.type')
    if obj.handle is not None and obj.handle != '':
        json_object['handle'] = obj.handle
    json_object['metadata'] = metadata
    return json_object
