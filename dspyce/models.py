from dspyce.entities.models import Relation
from dspyce.metadata.models import MetaData, MetaDataValue


class DSpaceObject:
    """
    The class DSpaceObject represents an Object in a DSpace repository, such as Items, Collections, Communities.
    """

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

    def add_metadata(self, tag: str, value: str, language: str = None):
        """
        Creates a new metadata field with the given value.

        :param tag: The correct metadata tag. The string must use the format <schema>.<element>.<qualifier>.
        :param value: The value of the metadata-field.
        :param language: The language of the metadata field.

        :raises KeyError: If the metadata tag doesn't use the format <schema>.<element>.<qualifier>.'
        """
        self.metadata[tag] = MetaDataValue(value, language)

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
        else:
            self.metadata[tag] = list(filter(lambda x: x.value != value, self.metadata[tag]))

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

    def __init__(self, uuid: str = '', handle: str = '', name: str = '', parent_community: DSpaceObject = None,
                 sub_communities: list[DSpaceObject] = None):
        super().__init__(uuid, handle, name)
        self.sub_communities = sub_communities if sub_communities is not None else []
        self.parent_community = parent_community

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


class Collection(DSpaceObject):
    """
    The class Collection represents a DSpace collection, containing different Items and having a parent community.
    """
    community: Community

    def __init__(self, uuid: str = '', handle: str = '', name: str = '', community: Community = None, ):
        super().__init__(uuid, handle, name)
        self.community = community

    def get_parent_community(self) -> Community:
        """
        Returns the parent community of the Collection, if existing.

        :return: Community object or None, if none existing.
        """
        return self.community

    def get_dspace_object_type(self) -> str:
        return 'Collection'


class Item(DSpaceObject):
    from dspyce.bitstreams.models import Bitstream, Bundle, IIIFBitstream
    """
    The class Item represents a single DSpace item. It can have a owning collection, several Bitstreams or relations
    to other items, if it's an entity.
    """
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
        self.relations.append(Relation(relation_type, (self, Item(uuid=identifier))))

    def add_content(self, content_file: str, path: str, description: str = '', bundle: str | Bundle = Bundle(),
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
        active_bundle = self.get_bundle(bundle.name if isinstance(bundle, self.Bundle) else bundle)
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

    def enable_entity(self, entity_type: str):
        """
        Enables an item to be a dspace-entity by providing an entity-type.

        :param entity_type: The type of the entity.
        """
        self.add_metadata('dspace.entity.type', entity_type)

    def get_owning_collection(self) -> Collection | None:
        """
        Provides the owning collection of the item, if existing.

        :return: The collection object of the owning collection or None.
        """
        return None if self.collections is None else self.collections[0]

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
