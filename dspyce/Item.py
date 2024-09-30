from dspyce.Collection import Collection
from dspyce.DSpaceObject import DSpaceObject
from dspyce.Relation import Relation
from dspyce.bitstreams import Bitstream, IIIFBitstream, Bundle


class Item(DSpaceObject):
    """
    The class Item represents a single DSpace item. It can have a owning collection, several Bitstreams or relations
    to other items, if it's an entity.
    """
    collections: list[Collection]
    relations: list[Relation]
    contents: list[Bitstream]
    bundles: list[Bundle]
    in_archive: bool = True
    discoverable: bool = True
    withdrawn: bool = False

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
        active_bundle = self.get_bundle(bundle.name if isinstance(bundle, Bundle) else bundle)
        if active_bundle is None:
            active_bundle = bundle if isinstance(bundle, Bundle) else Bundle(bundle)
            self.bundles.append(active_bundle)

        if iiif:
            cf = IIIFBitstream(content_file, path, bundle=bundle)
            name = content_file.split('.')[0]
            cf.add_iiif(description, name if iiif_toc == '' else iiif_toc, w=width)
            if self.metadata.get('dspace.iiif.enabled') is None:
                self.add_metadata('dspace.iiif.enabled', 'true', 'en')
        else:
            cf = Bitstream(content_file, path, bundle=bundle)

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
