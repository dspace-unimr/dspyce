from . import DSpaceObject
from . import Community


class Collection(DSpaceObject):
    community: Community

    def __init__(self, community: Community, uuid: str = '', handle: str = ''):
        super().__init__(uuid, handle)
        self.community = community
