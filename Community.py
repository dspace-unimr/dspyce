from . import DSpaceObject


class Community(DSpaceObject):
    sub_communities: list[DSpaceObject]

    def __init__(self, uuid: str = '', handle: str = '', name: str = '', sub_communities: list[DSpaceObject] = None):
        super().__init__(uuid, handle, name)
        self.sub_communities = sub_communities if sub_communities is not None else []

    def is_subcommunity_of(self, other) -> bool:
        """
        Checks if the community object is a sub-community of the given community.
        :param other: Another community object.
        :return: True, if self is in other.sub_communities.
        """
        if type(other) is not Community:
            raise TypeError('The given object must be of the type "Community".')
        else:
            return self in other.sub_communities
