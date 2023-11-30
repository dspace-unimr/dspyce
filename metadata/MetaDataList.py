from . import MetaData


class MetaDataList(list):
    """
    A list of metadata fields. Provides all methods of a classic list, but only for MetaData objects. If an object is
    appended to the list. The MetaDataList checks first, if there is already a metadata field with this tag.
    """
    def __init__(self, iterable: list[MetaData]):
        super().__init__(iterable)

    def __setitem__(self, index, item: MetaData):
        if not isinstance(item, MetaData):
            raise TypeError('Only items from type MetaData can be added to this list.')
        super().__setitem__(index, item)

    def insert(self, index, item: MetaData):
        if not isinstance(item, MetaData):
            raise TypeError('Only items from type MetaData can be added to this list.')
        super().insert(index, item)

    def append(self, item: MetaData):
        if not isinstance(item, MetaData):
            raise TypeError('Only items from type MetaData can be added to this list.')
        for i in range(len(self)):
            if item.is_field(self[i]):
                self[i].add_value(item.value)
                return
        super().append(item)

    def extend(self, other):
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            raise TypeError('The type of the other list must correspond to MetadataList')

    def __str__(self):
        return [str(i) for i in self]

    def __add__(self, other):
        if isinstance(other, type(self)):
            super().__add__(other)
        else:
            raise TypeError('The type of the other list must correspond to MetadataList')

    def get(self, tag: str):
        """
        Returns the value of a given metadata field.

        :param tag: The name of the metadata field. <schema>.<element>.<qualifier>
        :return: The value of the metadata field, or None if it doesn't exist.
        """
        for i in self:
            if i.is_field(tag):
                return i.value
        return None

    def get_schemas(self) -> list[str]:
        """
        Creates a list of used schemas in the metadata list.

        :return: A list of schema names a strings.
        """
        return [i.schema for i in self]