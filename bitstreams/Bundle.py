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

    def __init__(self, name: str = DEFAULT_BUNDLE, uuid: str = None):
        """
        Creates a new bundle object.

        :param name: The bundle name.
        :param uuid: The uuid of the bundle, if known.
        """
        self.name = name
        self.uuid = uuid

    def __str__(self):
        return self.name
