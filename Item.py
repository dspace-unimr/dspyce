from .Collection import Collection
from .DSpaceObject import DSpaceObject
from .Relation import Relation
from .bitstreams import ContentFile, IIIFContent, Bundle


class Item(DSpaceObject):
    collections: list[Collection]
    relations: list[Relation]
    contents: list[ContentFile]
    in_archive: bool = True
    discoverable: bool = True
    withdrawn: bool = False

    def __init__(self, uuid: str = '', handle: str = '', name: str = '',
                 collections: Collection | list[Collection] | str = None):
        """
        Creates a new object of the Item class.

        :param uuid: The uuid of the Item.
        :param handle: The handle of the Item.
        :param name: The name of the DSpace Item.
        :param collections: Collections connected to this item. The first collection in the list will be the owning
        collection. Just a uuid can also be provided.
        """
        super().__init__(uuid, handle, name)
        if type(collections) is str:
            self.collections = [Collection(uuid=collections, community=None)]
        elif type(collections) is Collection:
            self.collections = [collections]
        elif collections is None:
            self.collections = []
        else:
            self.collections = collections
            self.relations = []
        self.contents = []

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
            return self.metadata.get('dspace.entity.type')
        else:
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
            raise TypeError('Could not add relations to a non entity item.')
        self.relations.append(Relation(relation_type, (self, Item(uuid=identifier))))

    def add_content(self, content_file: str, path: str, description: str = '', bundle: str = '',
                    permissions: list[tuple[str, str]] = None, iiif: bool = False, width: int = 0, iiif_toc: str = ''):
        """
        Adds additional content-files to the item.

        :param content_file: The name of the document, which should be added.
        :param path: The path where to find the document.
        :param description: A description of the content file.
        :param bundle: The bundle where the item is stored in.
        :param permissions: Add permissions to a content file. This variable expects a list of tuples containing the
        permission-type and the group name to which it is granted to.
        :param iiif: If the bitstream should be treated as an iiif-specific file.
        :param width: The width of an image. Only needed, if the file is a jpg, wich should be reduced and iiif is True.
        :param iiif_toc: A toc information for an iiif-specific bitstream.
        """

        if iiif:
            cf = IIIFContent('images', content_file, path, bundle=bundle)
            name = content_file.split('.')[0]
            cf.add_iiif(description, name if iiif_toc == '' else iiif_toc, w=width)
        else:
            cf = ContentFile('other', content_file, path, bundle=bundle)

        if description != '':
            cf.add_description(description)
        if permissions is not None:
            for p in permissions:
                cf.add_permission(p[0], p[1])
        self.contents.append(cf)

    def enable_entity(self, entity_type: str):
        """
        Enables an item to be a dspace-entity by providing an entity-type.

        :param entity_type: The type of the entity.
        """
        self.add_metadata('dspace', 'entity', 'type', entity_type)

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

    def get_dspace_object_type(self) -> str:
        return 'Item'
