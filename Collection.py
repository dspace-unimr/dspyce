from .DSpaceObject import DSpaceObject
from .Community import Community


class Collection(DSpaceObject):
    community: Community

    def __init__(self, uuid: str = '', handle: str = '', name: str = '', community: Community = None, ):
        super().__init__(uuid, handle, name)
        self.community = community

    def get_parent_community(self) -> Community:
        return self.community

    def get_dspace_object_type(self) -> str:
        return 'Collection'
