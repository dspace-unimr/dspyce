from . import DSpaceObject
from . import Community


class Collection(DSpaceObject):
    community: Community

    def __init__(self, community: Community = None, uuid: str = '', handle: str = '', name: str = ''):
        super().__init__(uuid, handle, name)
        self.community = community

    def get_parent_community(self) -> Community:
        return self.community

    def get_dspace_object_type(self) -> str:
        return 'Collection'
