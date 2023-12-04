from . import DSpaceObject
from . import Community


class Collection(DSpaceObject):
    community: Community

    def __init__(self, community: Community, uuid: str = '', handle: str = '', name: str = ''):
        super().__init__(uuid, handle, name)
        self.community = community
