from .DSpaceObject import DSpaceObject
from .Community import Community


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
