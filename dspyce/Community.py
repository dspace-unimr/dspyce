from .DSpaceObject import DSpaceObject


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
