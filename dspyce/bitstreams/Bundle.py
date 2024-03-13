from .ContentFile import Bitstream


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
    bitstreams: list[Bitstream]
    """A list of bitstream associated with the bundle"""

    def __init__(self, name: str = DEFAULT_BUNDLE, description: str = '', uuid: str = None,
                 bitstreams: list[Bitstream] = None):
        """
        Creates a new bundle object.

        :param name: The bundle name.
        :param description: A description if existing.
        :param uuid: The uuid of the bundle, if known.
        :param bitstreams: A list of bitstreams associated with this bundle.
        """
        self.name = name
        self.uuid = uuid
        self.description = description
        self.bitstreams = []
        if bitstreams is not None:
            [self.add_bitstream(b) for b in bitstreams]

    def __str__(self):
        return 'Bundle: ' + self.name + (' - ' + self.uuid if self.uuid is not None else '')

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

        return self.uuid == other.uuid and self.name == other.name

    def get_bitstreams(self, filter_condition=lambda x: True) -> list[Bitstream]:
        """
        Returns a list of bitstreams in this bundle, filtered by a filter defined in filter_condition.

        :param filter_condition: A condition to filter the bitstreams returned.
        :return: A list of Bitstream objects.
        """
        return list(filter(filter_condition, self.bitstreams))

    def add_bitstream(self, bitstream: Bitstream):
        """
        Adds a bitstream to this bundle.

        :param bitstream: The bitstream to add.
        """
        bitstream.bundle = self
        self.bitstreams.append(bitstream)

    def remove_bitstream(self, bitstream: Bitstream):
        """
        Removes a bitstream from the current bundle. Raises an Exception if the bitstream does not exist.

        :param bitstream: The bitstream to remove from the bundle.
        :raises FileNotFoundError: If the bitstream does not exist.
        """
        self.bitstreams.remove(bitstream)
