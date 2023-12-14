class Bundle:
    """
    The class Bundle represents a bundle in the DSpace context. I can contain several bitstreams.
    """

    uuid: str | None
    """The uuid of the bundle"""
    DEFAULT_BUNDLE: str = 'ORIGINAL'
    """The default bundle name."""
    name: str
    """The bundle name."""
    description: str
    """A bundle description if existing."""

    def __init__(self, name: str = DEFAULT_BUNDLE, description: str = '', uuid: str = None):
        """
        Creates a new bundle object.

        :param name: The bundle name.
        :param description: A description if existing.
        :param uuid: The uuid of the bundle, if known.
        """
        self.name = name
        self.uuid = uuid
        self.description = description

    def __str__(self):
        return self.name

    def __eq__(self, other) -> bool:
        """
        Check if two bundle objects are equal

        :param other: The other bundle object to compare with.
        :return: True, if the two bundles have the same name.
        """
        if not isinstance(other, Bundle):
            raise TypeError(f'Can not compare type Bundle to "{type(other)}"')
        if self.uuid is None or other.uuid is None:
            return self.name == other.name
        else:
            return self.uuid == other.uuid and self.name == other.name
