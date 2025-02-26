import logging
from json import JSONDecodeError

import requests
from dspyce.metadata.models import MetaData, MetaDataValue


class DSpaceObject:
    """
    The class DSpaceObject represents an Object in a DSpace repository, such as Items, Collections, Communities.
    """
    """The MetaData and MetaDataValue classes used."""

    uuid: str
    """The uuid of the DSpaceObject"""
    name: str
    """The name of the DSpaceObject, if existing"""
    handle: str
    """The handle of the Object"""
    metadata: MetaData
    """The metadata provided for the object."""
    statistic_reports: dict
    """A dictionary of statistic report objects."""
    TYPES: tuple[str] = ('item', 'community', 'collection', 'bundle', 'bitstream')
    """A constant given information of all existing DSpaceObject types."""
    _metadata_updates: list[dict] = []
    """A private variable storing metadata update operations"""
    _track_updates: bool = False
    """A boolean value giving information about whether to track updates, to the current DSpace Object."""

    def __init__(self, uuid: str = '', handle: str = '', name: str = ''):
        """
        Creates a new object of the class DSpaceObject

        :param uuid: The uuid of the DSpaceObject. Default is ''
        :param handle: The handle of the DSpaceObject. Default is ''
        :param name: The name of the DSpaceObject, if existing.
        """
        self.uuid = uuid
        self.handle = handle
        self.name = name
        self.metadata = MetaData({})
        self.statistic_reports = {}

    def _store_metadata_update(self, operation: str, data: any, position = None):
        """
        Stores a metadata update operation into the _metadata_updates variable.
        :param operation: The update operation performed (add, remove, replace, move)
        """
        obj_type = self.get_dspace_object_type()
        self._metadata_updates.append({
            'operation': operation,
            'object_uuid': self.uuid,
            'obj_type': obj_type.lower() if isinstance(obj_type, str) else obj_type
        })
        if operation in ('delete', 'move'):
            self._metadata_updates[-1]['tag'] = data
        else:
            self._metadata_updates[-1]['metadata'] = data
        if position is not None:
            if operation == 'add':
                self._metadata_updates[-1]['position_end'] = position
            elif operation == 'move':
                self._metadata_updates[-1]['current_position'] = position[0]
                self._metadata_updates[-1]['target_position'] = position[1]
            else:
                self._metadata_updates[-1]['position'] = position
        return

    @staticmethod
    def get_from_rest(rest_api, uuid: str, obj_type: str, identifier: str = None):
        """
        Retrieves a new DSpaceObject by its uuid from the RestAPI.
        :param rest_api: The rest API object to use.
        :param uuid: The uuid of the DSpaceObject to retrieve.
        :param obj_type: The type of the DSpaceObject to retrieve, must be one of (Item, Community, Collection, Bundle,
            Bitstream).
        :param identifier: An optional other identifier to retrieve a DSpace Object. Can be used instead of uuid. Must
            be a handle or doi.
        :return: The DSpaceObject retrieved.
        :raises ValueError: if obj_type is unknown.
        :raises RestObjectNotFoundError: if the object identified by uuid or identifier was not found.
        """
        from dspyce.rest.functions import json_to_object
        from dspyce.rest.exceptions import RestObjectNotFoundError

        if obj_type not in DSpaceObject.TYPES:
            raise ValueError(f'DSpaceObject type {obj_type} not supported.')
        if obj_type[-1] == 'y':
            obj_type = obj_type[:-1] + 'ie'
        if identifier is None:
            if uuid == '' or not isinstance(uuid, str):
                raise ValueError(f'If no other identifier is used, the uuid must be provided. "{uuid}" is not correct.')
            params = {}
            url = f'core/{obj_type}s/{uuid}'
        else:
            url = 'pid/find'
            params = {'id': identifier}
        try:
            obj = json_to_object(rest_api.get_api(url, params))
            logging.debug(f'Retrieved DSpaceObject: {obj}')
        except RestObjectNotFoundError as e:
            if identifier is not None:
                e.add_note('Could get DSpaceObject by using identifier "%s".' % identifier)
            else:
                e.add_note('Could get DSpaceObject by using uuid "%s".' % uuid)
            raise e
        return obj

    def to_rest(self, rest_api):
        """
        Creates a new object in the given DSpace repository and updates this object based on the returned metadata.
        :param rest_api: The rest API object to use.
        :raises ConnectionRefusedError: If the rest API object did not provide authentication information.
        :raises TypeError: If the current DSpaceObject type does not exist.
        :raises ValueError: If the curren DSpaceObject already has a uuid.
        """
        from dspyce.rest.functions import json_to_object
        if not rest_api.authenticated:
            logging.critical('Could not add object, authentication required!')
            raise ConnectionRefusedError('Authentication needed.')
        if self.uuid is not None and self.uuid != '':
            raise ValueError(f'The current {self.get_dspace_object_type()} already has an uuid. It might exist already '
                             'in the DSpace repository')
        params = {}
        match self.get_dspace_object_type():
            case 'Item':
                self: Item
                add_url = f'{rest_api.api_endpoint}/core/items'
                params = {'owningCollection': self.get_owning_collection().uuid}
            case 'Community':
                self: Community
                if self.parent_community is None:
                    add_url = f'{rest_api.api_endpoint}/core/communities'
                else:
                    add_url = f'{rest_api.api_endpoint}/core/communities'
                    params = {'parent': self.parent_community.uuid}
            case 'Collection':
                self: Collection
                add_url = f'{rest_api.api_endpoint}/core/collections'
                params = {'parent': self.community.uuid}
            case _:
                raise TypeError(f'Object type {self.get_dspace_object_type()} is not allowed as a parameter!')
        obj_json = rest_api.post_api(add_url, data=self.to_dict(), params=params)
        obj = json_to_object(obj_json)
        self.uuid = obj.uuid
        self.handle = obj.handle
        self.metadata = obj.metadata
        self.name = obj.name
        self.reset_metadata_update()

    def add_metadata(self, tag: str, value: str | MetaDataValue, language: str = None, authority: str = None,
                     confidence: int = -1):
        """
        Creates a new metadata field with the given value.

        :param tag: The correct metadata tag. The string must use the format <schema>.<element>.<qualifier>.
        :param value: The value of the metadata-field. Can be either a string or a MetaDataValue object.
        :param language: The language of the metadata field.
        :param authority: The authority of the metadata field.
        :param confidence: The confidence of the metadata field.
        :raises KeyError: If the metadata tag doesn't use the format '<schema>.<element>.<qualifier>.'
        """
        value = value if isinstance(value, MetaDataValue) else MetaDataValue(value, language, authority, confidence)
        self.metadata[tag] = value
        if self._track_updates:
            self._store_metadata_update('add', {tag: [dict(value)]}, True)

    def remove_metadata(self, tag: str, value: str = None):
        """
        Remove a specific metadata field from the DSpaceObject. Can either be all values for a field or ony a specific
        value based on the *value* parameter.

        :param tag: The correct metadata tag. The string must use the format <schema>.<element>.<qualifier>.
        :param value: The value of the metadata field to delete. Can be used, if only one value in a list of values
            should be deleted. If None, all values from the given tag will be deleted.
        """
        if value is None:
            self.metadata.pop(tag)
            if self._track_updates:
                self._store_metadata_update('delete', tag, -1)
        else:
            try:
                position = [i.value for i in self.metadata[tag]].index(value)
            except ValueError:
                return
            while position is not None:
                self.metadata[tag].pop(position)
                if self._track_updates:
                    self._store_metadata_update('delete', tag, position)
                try:
                    position = [i.value for i in self.metadata[tag]].index(value)
                except ValueError:
                    return

    def replace_metadata(self, tag: str, value: str, language: str = None):
        """
        Replaces a specific metadata field from the DSpaceObject. Replaces all values of a given tag.

        :param tag: The correct metadata tag. The string must use the format <schema>.<element>.<qualifier>.
        :param value: The value of the metadata field to add. Can be used, if only one value in a list of values
            should be deleted. If None, all values from the given tag will be deleted.
        :param language: The language of the metadata value to add.
        """
        self.remove_metadata(tag)
        self.add_metadata(tag, value, language)

    def move_metadata(self, tag: str, from_position: int, to_position: int):
        """
        Moves the MetadataValue object from the given postion to the given "to_position" position.
        :param tag: The metadata tag.
        :param from_position: The original position of the metadata value to move.
        :param to_position: The new position of the metadata value to move (-1 to move it at the end of the array).
        :raises KeyError: If the from_position doesn't exist in the object's metadata.
        :raises IndexError: If the to_position is higher than the length of the metadataValue list.
        """
        md = self.get_metadata(tag)
        if len(md) == 0 or from_position >= len(md):
            raise KeyError('The position of the metadata value to move is out of range or the MetadataValue does not'
                           'exist')
        if to_position >= len(md) or to_position <= (len(md)*-1):
            raise IndexError('The target position of the MetadataValue to move is out of range for the metadata list.')
        value = md.pop(from_position)
        md = md[:to_position] + [value] + md[to_position:]
        self.metadata[tag] = md
        if self._track_updates:
            self._store_metadata_update('move', tag, (from_position, to_position))

    def track_updates(self):
        """
        Start tracking all metadata updates in order to reproduce them at a later call of the update_metadata_rest()
        method.
        :raises AttributeError: If uuid is not set.
        """
        if self.uuid is None or self.uuid == '':
            raise AttributeError('The UUID must be set for tracking updates.')
        self._track_updates = True
        self.reset_metadata_update()

    def stop_tracking_updates(self):
        """
        Stop tracking metadata updates.
        """
        self._track_updates = False
        self.reset_metadata_update()

    def reset_metadata_update(self):
        """
        Resets the current metadata update tracker and removes all values from _metadata_udpates.
        """
        self._metadata_updates = []

    def update_metadata_rest(self, rest, stop_tracking: bool = True):
        """
        Updates the metadata fields of the current object in the given restAPI based on the actions traced in the
        _metadata_updates list.
        :param rest: The rest api to use.
        :param stop_tracking: Whether to stop tracking metadata updates.
        :raises AttributeError: If an unknown operation is called.
        """
        for i in self._metadata_updates:
            operation = i.get('operation')
            i.pop('operation')
            logging.debug('Performing %s operation with values: %s' % (operation, str(i)))
            match operation:
                case 'add': rest.add_metadata(**i)
                case 'delete': rest.delete_metadata(**i)
                case 'move': rest.move_metadata(**i)
                case _: raise AttributeError('Could not perform operation "%s", unknown.' % operation)
        self.reset_metadata_update()
        if stop_tracking:
            self.stop_tracking_updates()

    def get_dspace_object_type(self) -> str:
        """
        This Function serves mainly to be overwritten by subclasses to get the type of DSpaceObject.
        """
        pass

    def get_identifier(self) -> str | None:
        """
        Returns the identifier of this object. Preferably this will be the uuid, but if this does not exist, it uses
        the handle.
        :return: The identifier as a string.
        """
        if self.uuid != '':
            return self.uuid
        if self.handle != '':
            return self.handle
        return None

    def __eq__(self, other):
        if self.uuid == '' and other.uuid == '' and self.handle == '' and other.handle == '':
            raise ValueError('Can not compare objects without a uuid or handle.')
        return (self.uuid == other.uuid) if self.uuid != '' else (self.handle == other.handle)

    def __str__(self):
        return f'DSpace object with the uuid {self.uuid}:\n\t' + '\n\t'.join(str(self.metadata).split('\n'))

    def to_dict(self) -> dict:
        """
            Converts the current item object to a dictionary object containing all available metadata.
        """
        obj_dict = {}
        if self.uuid != '':
            obj_dict['uuid'] = self.uuid
        if self.handle != '':
            obj_dict['handle'] = self.handle
        if self.name != '':
            obj_dict['name'] = self.name
        if self.get_dspace_object_type() is not None:
            obj_dict['type'] = self.get_dspace_object_type().lower()
        obj_dict['metadata'] = self.metadata.to_dict()
        return obj_dict

    def has_metadata(self, tag: str) -> bool:
        """
        Checks whether this object has a specific metadata field.
        :param tag: The metadata tag to check.
        :returns: True if the metadata field exists, False otherwise.
        """
        return tag in self.metadata.keys()

    def get_metadata(self, tag: str) -> list[MetaDataValue]:
        """
        Retrieves a list of MetadataValue objects for the given tag.
        :param tag: The tag to get the metadata for.
        :return: A list of MetadataValue objects.
        """
        md = self.metadata.get(tag)
        return [] if md is None else md

    def get_metadata_values(self, tag: str) -> list | None:
        """
        Retrieves the metadata values of a specific tag as a list.

        :param tag: The metadata tag: prefix.element.qualifier
        :return: The values as a list or None, if the tag doesn't exist.
        """
        m = self.get_metadata(tag)
        return [v.value for v in m] if len(m) > 0 else None

    def get_first_metadata(self, tag: str) -> MetaDataValue | None:
        """
        Retrieve the first metadata value of a specific metadata field.
        """
        md = self.get_metadata(tag)
        return md[0] if len(md) > 0 else None

    def get_first_metadata_value(self, tag: str) -> str | None:
        """
        Retrieve the first metadata value of a specific metadata field.
        """
        return self.get_metadata_values(tag)[0] if self.get_metadata_values(tag) is not None else None

    def add_statistic_report(self, report: dict | list[dict] | None):
        """
        Adds a new report or list of reports as a dict object to the DSpaceObject

        :param report: The report(s) to add.
        """
        if report is None:
            return
        report = [report] if isinstance(report, dict) else report
        for r in report:
            for k in r.keys():
                if k not in self.statistic_reports.keys():
                    self.statistic_reports[k] = r[k]
                else:
                    if isinstance(r[k], dict):
                        self.statistic_reports[k] = (self.statistic_reports[k] +
                                                     [r[k]]) if isinstance(self.statistic_reports[k],
                                                                           list) else [self.statistic_reports[k], r[k]]
                    else:
                        self.statistic_reports[k] = r[k]

    def has_statistics(self) -> bool:
        """
        Checks if statistic reports are available for this object.

        :return: True if there is at least one report.
        """
        return len(self.statistic_reports.keys()) > 0


class Community(DSpaceObject):
    """
    The class Community represents a DSpace community containing sub communities or collections.
    """
    parent_community: DSpaceObject | None
    sub_communities: list[DSpaceObject]
    sub_collections: list[DSpaceObject]

    def __init__(self, uuid: str = '', handle: str = '', name: str = '', parent_community: DSpaceObject = None,
                 sub_communities: list[DSpaceObject] = None):
        super().__init__(uuid, handle, name)
        self.sub_communities = sub_communities if sub_communities is not None else []
        self.parent_community = parent_community

    @staticmethod
    def get_from_rest(rest_api, uuid: str, obj_type: str='community', identifier: str = None):
        """
        Retrieves a new Community by its uuid from the RestAPI.
        :param rest_api: The rest API object to use.
        :param uuid: The uuid of the Community to retrieve.
        :param obj_type: The type of the Community to retrieve, must be 'community'.
        :param identifier: An optional other identifier to retrieve a DSpace Object. Can be used instead of uuid. Must
            be a handle.
        :return: The Community retrieved.
        :raises ValueError: If the obj_type is not 'community'.
        :raises RestObjectNotFoundError: if the object identified by uuid or identifier was not found.
        """
        if obj_type != 'community':
            raise ValueError('obj_type parameter must be "community", but got %s.' % obj_type)
        dso = DSpaceObject.get_from_rest(rest_api, uuid, obj_type, identifier)
        dso.get_parent_community_from_rest(rest_api)
        logging.debug(f'Successfully retrieved community {dso} from endpoint.')
        return dso

    def get_parent_community_from_rest(self, rest_api):
        """
        Retrieves the parent community of the community from a given REST API.
        :param rest_api: The rest API object to use.
        """
        from dspyce.rest.exceptions import RestObjectNotFoundError
        from dspyce.rest.functions import json_to_object
        url = f'core/communities/{self.uuid}/parentCommunity'
        try:
            get_result = rest_api.get_api(url)
        except RestObjectNotFoundError:
            return
        except JSONDecodeError:
            return
        if get_result is None:
            logging.warning(f'Did not found a parent community for community {self}.')
            return None
        self.parent_community = json_to_object(get_result)

    def get_subcommunities_from_rest(self, rest_api, in_place: bool = True):
        """
        Retrieves all sub communities from the current community.
        :param rest_api: The rest API object to use.
        :param in_place: If True, the returned object will be placed into the current community.
        :return: A list of sub communities if in_place i False, None otherwise.
        """
        from dspyce.rest.functions import json_to_object
        url = f'/core/communities/{self.uuid}/subcommunities'
        objs = rest_api.get_paginated_objects(url, 'subcommunities')
        logging.debug('Retrieved %i subcommunities for community %s.', len(objs), self.uuid)
        objs = [json_to_object(o) for o in objs]
        if not in_place:
            return objs
        self.sub_communities = objs

    def get_subcollections_from_rest(self, rest_api, in_place: bool = True):
        """
        Retrieves all sub collections from the current community.
        :param rest_api: The rest API object to use.
        :param in_place: If True, the returned object will be placed into the current community.
        :return: A list of sub collection if in_place i False, None otherwise.
        """
        from dspyce.rest.functions import json_to_object
        url = f'/core/communities/{self.uuid}/collections'
        objs = rest_api.get_paginated_objects(url, 'collections')
        logging.debug('Retrieved %i collections for community %s.', len(objs), self.uuid)
        objs = [json_to_object(o) for o in objs]
        if not in_place:
            return objs
        self.sub_collections = objs

    def to_rest(self, rest_api):
        """
        Creates a new Community object in the given DSpace repository.
        :param rest_api: The rest API object to use.
        """
        if self.parent_community is not None and self.parent_community.uuid == '':
            raise ValueError('The parent community must already exist in DSpace. Consider calling '
                             'add_parrent_communities() first.')
        super().to_rest(rest_api)
        logging.debug('Successfully created new Community object with uuid "%s".' % self.uuid)

    def add_parent_communities_to_rest(self, rest_api):
        """
        Adds all parent communities of the given community to the given DSpace repository.
        :param rest_api: The rest API object to use.
        """
        if self.parent_community is not None and self.parent_community.uuid == '':
            self.parent_community.add_parent_communities_to_rest(rest_api)
            self.parent_community.to_rest(rest_api)

    def is_subcommunity_of(self, other) -> bool:
        """
        Checks if the community object is a sub-community of the given community.
        :param other: Another community object.
        :return: True, if self is in other.sub_communities.
        """
        if not isinstance(other, Community):
            raise TypeError('The given object must be of the type "Community".')
        return self in other.sub_communities

    def get_dspace_object_type(self) -> str:
        return 'Community'

    def delete(self, rest_api, all_objects: bool = False):
        """
        Deletes the current community from the given rest_api. Raises an error, if the community still includes items or
        collections and all_objects is set to false.
        :param rest_api: The rest api object to use.
        :param all_objects: Whether to delete all items and collections in the community as well.
        :raises AttributeError: If community still includes items or collections and all_objects is set to false.
        """
        rest_api.delete_community(self, all_objects)
        self.uuid = ''


class Collection(DSpaceObject):
    """
    The class Collection represents a DSpace collection, containing different Items and having a parent community.
    """
    community: Community

    def __init__(self, uuid: str = '', handle: str = '', name: str = '', community: Community = None, ):
        super().__init__(uuid, handle, name)
        self.community = community

    @staticmethod
    def get_from_rest(rest_api, uuid: str, obj_type: str='collection', identifier: str = None):
        """
        Retrieves a new Collection by its uuid from the RestAPI.
        :param rest_api: The rest API object to use.
        :param uuid: The uuid of the Collection to retrieve.
        :param obj_type: The type of the Collection to retrieve, must be 'collection'.
        :param identifier: An optional other identifier to retrieve a DSpace Object. Can be used instead of uuid. Must
            be a handle.
        :return: The Collection retrieved.
        :raises ValueError: If the obj_type is not 'collection'.
        :raises RestObjectNotFoundError: if the object identified by uuid or identifier was not found.
        """
        if obj_type != 'collection':
            raise ValueError('obj_type parameter must be "collection", but got %s.' % obj_type)
        dso = DSpaceObject.get_from_rest(rest_api, uuid, obj_type, identifier)
        dso.get_parent_community_from_rest(rest_api)
        logging.debug(f'Successfully retrieved collection {dso} from endpoint.')
        return dso

    def get_parent_community_from_rest(self, rest_api):
        """
        Retrieves the parent community of the collection from a given REST API.
        :param rest_api: The rest API object to use.
        :raises RestObjectNotFoundError: If no parent community was found.
        """
        from dspyce.rest.functions import json_to_object
        url = f'core/collections/{self.uuid}/parentCommunity'
        get_result = rest_api.get_api(url)
        self.community = json_to_object(get_result)

    def to_rest(self, rest_api):
        """
        Creates a new Collection object in the given DSpace repository.
        :param rest_api: The rest API object to use.
        """
        if self.community is not None and self.community.uuid == '':
            raise ValueError('The parent community must already exist in DSpace. Consider calling '
                             'add_parent_communities() first.')
        super().to_rest(rest_api)
        logging.debug('Successfully created new Collection object with uuid "%s".' % self.uuid)

    def add_parent_communities_to_rest(self, rest_api):
        """
        Adds all parent communities of the given community to the given DSpace repository.
        :param rest_api: The rest API object to use.
        """
        if self.community is not None and self.community.uuid == '':
            self.community.add_parent_communities_to_rest(rest_api)
            self.community.to_rest(rest_api)

    def get_items(self, rest_api) -> list:
        """
        Retrieves all items stored in this collection from the given rest API.
        :param rest_api: The rest api to use.
        :return: A list of Items.
        """
        return rest_api.get_objects_in_scope(self.uuid)

    def get_parent_community(self) -> Community:
        """
        Returns the parent community of the Collection, if existing.

        :return: Community object or None, if none existing.
        """
        return self.community

    def get_dspace_object_type(self) -> str:
        return 'Collection'

    def delete(self, rest_api, all_items: bool = False):
        """
        Deletes the current collection from the given rest_api. Raises an error, if the collection still includes items
        and all_items is set to false.
        :param rest_api: The rest api object to use.
        :param all_items: Whether to delete all items in the collection as well.
        :raises AttributeError: If collection still includes items and all_items is set to false.
        """
        rest_api.delete_collection(self, all_items)
        self.uuid = ''


class Item(DSpaceObject):
    """
    The class Item represents a single DSpace item. It can have a owning collection, several Bitstreams or relations
    to other items, if it's an entity.
    """
    from dspyce.bitstreams.models import Bitstream, Bundle, IIIFBitstream
    """Bitstream, Bundle and IIIF for Item objects"""
    from dspyce.entities.models import Relation
    """The Relation Class connected to Items"""
    collections: list[Collection]
    """Collections where this item belongs."""
    relations: list[Relation]
    """The relations of the item."""
    contents: list[Bitstream]
    """The list of bitstreams for this item."""
    bundles: list[Bundle]
    """The list of bundles for this item."""
    in_archive: bool = True
    """Whether an item is archived in DSpace."""
    discoverable: bool = True
    """Whether an item is discoverable in DSpace."""
    withdrawn: bool = False
    """Whether an item is withdrawn from DSpace."""

    def __init__(self, uuid: str = '', handle: str = '', name: str = '',
                 collections: Collection | list[Collection] | str = None):
        """
        Creates a new object of the Item class.

        :param uuid: The uuid of the Item.
        :param handle: The handle of the Item.
        :param name: The name of the DSpace Item, if existing.
        :param collections: Collections connected to this item. The first collection in the list will be the owning
        collection. Just an uuid can also be provided.
        """
        super().__init__(uuid, handle, name)
        if isinstance(collections, str):
            self.collections = [Collection(uuid=collections, community=None)]
        elif isinstance(collections, Collection):
            self.collections = [collections]
        elif collections is None:
            self.collections = []
        else:
            self.collections = collections
        self.relations = []
        self.contents = []
        self.bundles = []

    @staticmethod
    def get_from_rest(rest_api, uuid: str, obj_type: str='item', identifier: str = None):
        """
        Retrieves a new Item by its uuid from the RestAPI.
        :param rest_api: The rest API object to use.
        :param uuid: The uuid of the Item to retrieve.
        :param obj_type: The type of the Item to retrieve, must be 'item'.
        :param identifier: An optional other identifier to retrieve a DSpace Object. Can be used instead of uuid. Must
            be a handle or a doi.
        :return: The Item retrieved.
        :raises ValueError: If the obj_type is not 'item'.
        :raises RestObjectNotFoundError: if the object identified by uuid or identifier was not found.
        """
        if obj_type != 'item':
            raise ValueError('obj_type parameter must be "item", but got %s.' % obj_type)
        dso = DSpaceObject.get_from_rest(rest_api, uuid, obj_type, identifier)
        dso.get_bundles_from_rest(rest_api)
        dso.get_collections_from_rest(rest_api)
        logging.debug(f'Successfully retrieved item {dso} from endpoint.')
        return dso

    def get_bundles_from_rest(self, rest_api, include_bitstreams: bool = True):
        """
        Retrieves all bundles for the item from the given REST API.
        :param rest_api: The rest API object to use.
        :param include_bitstreams: Whether bitstreams should be downloaded as well. Default: True
        """
        from dspyce.rest.functions import json_to_object

        dspace_objects = [json_to_object(obj)
                          for obj in rest_api.get_paginated_objects(f'/core/items/{self.uuid}/bundles', 'bundles')]
        for d in dspace_objects:
            if not isinstance(d, self.Bundle):
                raise TypeError('Object %s in the bundle list is not of type bundle. Found type "%s".' % (d, type(d)))
            if include_bitstreams:
                d.get_bitstreams_from_rest(rest_api)
        self.bundles = dspace_objects
        self.contents = []
        for b in dspace_objects:
            self.contents += b.get_bitstreams()

    def get_collections_from_rest(self, rest_api):
        """
        Retrieves a list of collections from the REST-API and adds them to the item object. The first will be the owning
        collection.
        :param rest_api: The rest API object to use.
        :raises DSpaceObjectNotFoundError: If no collection could be found.
        """
        from dspyce.rest.functions import json_to_object
        url = f'core/items/{self.uuid}/owningCollection'
        get_result = rest_api.get_api(url)
        owning_collection = json_to_object(get_result)
        mapped_collections = rest_api.get_paginated_objects(f'core/items/{self.uuid}/mappedCollections',
                                                        'mappedCollections')
        self.collections = [owning_collection] + list(filter(lambda x: x is not None,
                                                             [json_to_object(m) for m in mapped_collections]))

    def get_relations_from_rest(self, rest_api):
        """
        Retrieves a list of relationships for the current item from the given REST API.
        :param rest_api: The rest API object to use.
        :raises TypeError: If the current Item is not an Entity.
        """
        from dspyce.entities.models import Relation
        if not self.is_entity():
            raise TypeError('The current Item is not an Entity.')

        url = f'/core/items/{self.uuid}/relationships'

        rel_list = rest_api.get_paginated_objects(url, 'relationships')
        relations = []
        for r in rel_list:
            left_item_uuid = r['_links']['leftItem']['href'].split('/')[-1]
            right_item_uuid = r['_links']['rightItem']['href'].split('/')[-1]
            direction = 'leftwardType' if self.uuid == right_item_uuid else 'rightwardType'
            # Retrieve the type information:
            type_req = rest_api.session.get(r['_links']['relationshipType']['href'])
            rel_key = type_req.json()[direction]
            rel_type = type_req.json()['id']
            # Set the correct item order.
            try:
                left_item = Item.get_from_rest(rest_api, left_item_uuid) if left_item_uuid != self.uuid else self
                right_item = Item.get_from_rest(rest_api, right_item_uuid) if right_item_uuid != self.uuid else self
                items = (left_item, right_item) if direction == 'rightwardType' else (right_item, left_item)
                relation = Relation(rel_key, items, rel_type)
                relations.append(relation)
                logging.debug(f'Retrieved relation {relation}.')
            except requests.exceptions.RequestException:
                logging.warning(f'Could not retrieve relationship({rel_key}) between {left_item_uuid} and'
                                f' {right_item_uuid}')
        logging.info('Found %i relationships for the item.' % (len(relations)))
        self.relations = relations

    def to_rest(self, rest_api):
        """
        Creates a new Collection object in the given DSpace repository.
        :param rest_api: The rest API object to use.
        :raises ValueError: If the collections of this item don't have an uuid yet or no Collection exists.
        """
        from dspyce.entities.models import Relation
        if len(self.collections) == 0:
            raise ValueError('Can not push an Item into the restAPI without information about the owning collections.')
        for c in self.collections:
            if c.uuid is None or c.uuid == '':
                raise ValueError('All collection must already exist in DSpace. Consider calling '
                                 'add_parent_collections() first.')
        super().to_rest(rest_api)
        if len(self.collections) > 1:
            self.add_to_mapped_collections(rest_api)
        self.add_bundles_to_rest(rest_api, True)
        if self.is_entity():
            relation_types = {
                r.relation_key: r.relation_type for r in Relation.get_by_type_from_rest(rest_api,
                                                                                        self.get_entity_type())
            }
            for r in self.relations:
                try:
                    r.relation_type = relation_types[r.relation_key]
                except KeyError as e:
                    e.add_note(f'Relationship with name "{r.relation_key}" does no exist in the given restAPI!')
                    raise e
                r.to_rest(rest_api)
        logging.debug('Successfully created new Item object with uuid "%s".' % self.uuid)

    def add_parent_collections_to_rest(self, rest_api):
        """
        Adds all parent collections and communities of the current item to the given DSpace repository.
        :param rest_api: The rest API object to use.
        """
        for c in self.collections:
            if c.uuid is None or c.uuid == '':
                c.add_parent_communities_to_rest(rest_api)
                c.to_rest(rest_api)

    def add_bundles_to_rest(self, rest_api, include_bitstreams: bool = True):
        """
        Adds all bundles of the current item to the given RestAPI.
        :param rest_api: The rest API object to use.
        :param include_bitstreams: If True, add all bitstreams in the bundle toe rest api as well.
        """
        for b in self.bundles:
            if b.uuid is None or b.uuid == '':
                b.to_rest(rest_api, self.uuid, include_bitstreams)
            else:
                logging.warning('The bundle %s can not be added to the rest API because it already has a uuid (%s).' \
                                % (b.name, b.uuid))

    def add_to_mapped_collections(self, rest_api, mapped_collections: list[Collection] = None):
        """
        Add the current item to its mapped collections in the given Rest API.
        :param rest_api: The rest API object to use.
        :param mapped_collections: A list of collections which should be added as mapped collections to the item first.
        """
        if mapped_collections is not None:
            self.add_mapped_collections(mapped_collections)
        if len(self.collections) <= 1:
            logging.warning('No mapped collections found. Do nothing.')
            return
        for c in self.collections[1:]:
            if c.uuid is None or c.uuid == '':
                raise ValueError(f'Mapped collection for item "{self.uuid}" has no uuid!')
        api_endpoint = f'{rest_api.api_endpoint}/core/items/{self.uuid}/mappedCollections'
        content_type = 'text/uri-list'
        collection_uris = []
        for c in self.get_mapped_collections():
            collection_uris.append(f'{rest_api.api_endpoint}/core/collections/{c.uuid}')
        if len(collection_uris) > 0:
            rest_api.post_api(api_endpoint, '\n'.join(collection_uris), {}, content_type=content_type)

    def is_entity(self) -> bool:
        """
        Checks if the item is a DSpace-Entity (True, if the metadata field dspace.entity.type is not empty).

        :return: True, if the Item is an entity.
        """
        return self.metadata.get('dspace.entity.type') is not None

    def get_entity_type(self) -> str | None:
        """
        Checks if the item is a DSpace-Entity and returns the value of dspace.entity.type if true, if not it returns
        None.

        :return: The entity type as a string, if existing, else None.
        """
        if self.is_entity():
            return self.get_metadata_values('dspace.entity.type')[0]

        return None

    def add_collection(self, c: Collection, primary: bool = False):
        """
        Adds an owning collection to the item. If primary is True, the collection will be set as the owning collection.
        :param c:
        :param primary:
        :return:
        """
        if primary:
            self.collections = [c] + self.collections
        else:
            self.collections.append(c)

    def add_relation(self, relation_type: str, identifier: str):
        """
        Adds a new relation to another item. Only possible if `is_entity()==True`.

        :param relation_type: The name of the relationship
        :param identifier: The identifier of the related Item.
        :return: None
        """
        if not self.is_entity():
            raise TypeError('Could not add relations to a non entity item for item:\n' + str(self))
        self.relations.append(self.Relation(relation_type, (self, Item(uuid=identifier))))

    def add_content(self, content_file: str, path: str, description: str = '', bundle = None,
                    permissions: list[tuple[str, str]] = None, iiif: bool = False, width: int = 0, iiif_toc: str = ''):
        """
        Adds additional content-files to the item.

        :param content_file: The name of the document, which should be added.
        :param path: The path where to find the document.
        :param description: A description of the content file.
        :param bundle: The bundle where the item is stored in. The default is bundle.DEFAULT_BUNDLE
        :param permissions: Add permissions to a content file. This variable expects a list of tuples containing the
            permission-type and the group name to which it is granted to.
        :param iiif: If the bitstream should be treated as an iiif-specific file. If true also "dspace.iiif.enabled"
            will be set to "true".
        :param width: The width of an image. Only needed, if the file is a jpg, wich should be reduced and iiif is True.
        :param iiif_toc: A toc information for an iiif-specific bitstream.
        """
        if bundle is None:
            bundle = self.Bundle(self.Bundle.DEFAULT_BUNDLE, '', '', [])
        active_bundle = self.get_bundle(
            bundle.name if isinstance(bundle, self.Bundle) else bundle
        )
        if active_bundle is None:
            active_bundle = bundle if isinstance(bundle, self.Bundle) else self.Bundle(bundle)
            self.bundles.append(active_bundle)

        if iiif:
            cf = self.IIIFBitstream(content_file, path, bundle=bundle)
            name = content_file.split('.')[0]
            cf.add_iiif(description, name if iiif_toc == '' else iiif_toc, w=width)
            if self.metadata.get('dspace.iiif.enabled') is None:
                self.add_metadata('dspace.iiif.enabled', 'true', 'en')
        else:
            cf = self.Bitstream(content_file, path, bundle=bundle)

        if description != '':
            cf.add_description(description)
        if permissions is not None:
            for p in permissions:
                cf.add_permission(p[0], p[1])
        self.contents.append(cf)
        active_bundle.add_bitstream(cf)

    def move_item(self, rest, new_collection: Collection = None):
        """
        Moves an item to a new collection (completely replacing the old one). If a collection is given as new
        collection, the item will be placed there, if None provided, the item will be moved into the current owning
        collection of the item.

        :param rest: The rest api object to use
        :param new_collection: The new collection to put the item. If None, uses the current owning collection as the
            new collection.
        """
        endpoint = f'core/items/{self.uuid}/owningCollection'
        collection_uuid = new_collection.uuid if new_collection is not None else self.get_owning_collection().uuid
        logging.info(f'Moving item with uuid {self.uuid} into new owning collection with uuid {collection_uuid}.')
        rest.put_api(endpoint, f'{rest.api_endpoint}/core/collections/{collection_uuid}', content_type='text/uri-list')
        if new_collection is not None:
            self.collections[0] = new_collection

    def remove_collection_mapping(self, rest, collection: Collection = None):
        """
        Remove the given collection as a mapped collection in the given rest api. If no collection is provided: removes
        all mapped collections of the current item in the given rest API.
        """
        if collection is not None:
            collection_uuid = collection.uuid
            logging.debug('Remove mapped collection (%s) from item (%s).' % (collection_uuid, self.uuid))
            rest.delete_api(f'core/items/{self.uuid}/mappedCollections/{collection_uuid}')
            self.collections = list(filter(lambda x: x != collection, self.collections))
        else:
            for c in self.get_mapped_collections():
                logging.debug('Remove mapped collection (%s) from item (%s).' % (c.uuid, self.uuid))
                rest.delete_api(f'core/items/{self.uuid}/mappedCollections/{c.uuid}')
            self.remove_mapped_collections()

    def enable_entity(self, entity_type: str):
        """
        Enables an item to be a dspace-entity by providing an entity-type.

        :param entity_type: The type of the entity.
        """
        self.add_metadata('dspace.entity.type', entity_type)

    def add_mapped_collections(self, collections: list[Collection]):
        """
        Add the given collections to the collection list of an item. The mapped collections do not get replaced but
        the new ones are appended to the existing ones. Only usable if the item has already an owning collection.
        :param collections: The mapped collections to append.
        :raises ValueError: If no owning collection exist.
        """
        if self.get_owning_collection() is None:
            raise ValueError('Could not add mapped collections if no owning collection exist!')
        self.collections += collections

    def remove_mapped_collections(self):
        """
        Removes all mapped collections of the current item.
        """
        self.collections = [self.get_owning_collection()]

    def get_owning_collection(self) -> Collection | None:
        """
        Provides the owning collection of the item, if existing.

        :return: The collection object of the owning collection or None.
        """
        return None if self.collections is None else self.collections[0]

    def get_mapped_collections(self) -> list[Collection]:
        """
        Provides the mapped collections of the item, if existing.

        :return: The collection objects.
        """
        return self.collections[1:] if len(self.collections) > 1 else []

    def get_bundles(self) -> list[Bundle]:
        """
        Returns the bundles used by this item.
        """
        bundles = []
        for c in self.contents:
            if c.bundle not in bundles:
                bundles.append(c.bundle)
        return bundles

    def get_bundle(self, bundle_name: str) -> Bundle | None:
        """
        Returns a specific bundle based on the bundle name or None if the bundle does not exist.

        :param bundle_name: The name of the bundle.
        :return: The bundle object associated with the bundle name, or None if a bundle with this name does not exist.
        """
        for b in self.bundles:
            if b.name == bundle_name:
                return b
        return None

    def add_bundle(self, bundle: Bundle):
        """
        Adds the given Bundle to the current Item.
        :raises KeyError: If the bundle already exists.
        """
        if bundle in self.bundles:
            raise KeyError('Could not add bundle %s to the item bundle, because it already exists.' % str(bundle))
        self.bundles.append(bundle)

    def get_bitstreams(self) -> list[Bitstream]:
        """
        Returns all bitstreams associated with the item.
        """
        bitstreams = []
        for b in self.get_bundles():
            bitstreams += b.get_bitstreams()
        return bitstreams

    def get_dspace_object_type(self) -> str:
        return 'Item'

    def __str__(self):
        """
        Creates a string representation of the item object.
        """
        obj_str = super().__str__()
        obj_str = obj_str.replace('DSpace object', 'DSpace item')
        if len(self.relations) > 0:
            obj_str += '\n\tRelations:'
            for r in self.relations:
                obj_str += f'\n\t\t{r}'
        if len(self.bundles) > 0:
            obj_str += '\n\tBitstreams:'
            for b in self.bundles:
                for c in b.bitstreams:
                    obj_str += f'\n\t\t{c}'
        if len(self.collections) > 0:
            obj_str += '\n\tCollections:'
            for c in self.collections:
                obj_str += f'\n\t\t{c.uuid if c.uuid != "" else c.handle}'
        return obj_str

    def get_related(self) -> list[DSpaceObject]:
        """
        If this Item is an entity. This method will return a list of related items. If not the list will be empty.

        :return: A list of DSpaceObjects (Items)
        """
        if not self.is_entity():
            return []
        return [r.items[1] for r in self.relations]

    def to_dict(self) -> dict:
        """
        Returns a rest-compatible dictionary representation of the item.
        """
        obj_dict = super().to_dict()
        obj_dict.update({'inArchive': self.in_archive, 'discoverable': self.discoverable, 'withdrawn': self.withdrawn})
        if self.is_entity():
            obj_dict['entityType'] = self.get_entity_type()
        return obj_dict

    def delete(self, rest_api, copy_virtual_metadata: bool = False, by_relationships: Relation | list[Relation] = None):
        """
        Deletes an item from the rest API by using its uuid. If you delete an item, you can request to transform
        possible virtual metadata fields for related items to real metadata fields. If you want to only transform
        virtual metadata fields of specific relations, you can add those relations.
        :param rest_api: The rest_api object to use.
        :param copy_virtual_metadata: Whether to copy virtual metadata of related items. Default: False.
        :param by_relationships: Relationships to copy the metadata for. If none provided and `copy_virtual_metadata` is
            True, all metadata will be copied.
        """
        params = {}
        if copy_virtual_metadata:
            if by_relationships is None:
                params['copyVirtualMetadata'] = 'all'
            else:
                params = '&'.join([f'copyVirtualMetadata={r.relation_type}' for r in by_relationships])
        rest_api.delete_api(f'core/items/{self.uuid}',  params)
        logging.info('Successfully deleted item with uuid "%s".' % self.uuid)
        self.uuid = ''
        for b in self.bundles:
            b.uuid = ''
            for bitstream in b.get_bitstreams():
                bitstream.uuid = ''

