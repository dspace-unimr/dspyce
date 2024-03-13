class MetaData:
    """
    This class represents a metadata field for a DSpace object. Containing information about the schema, element,
    qualifier and value.
    """

    schema: str
    element: str
    qualifier: str
    language: str | None
    value: any

    def __init__(self, schema: str, element: str, qualifier: str | None, value, language: str = None):
        """
        Creates a new MetaData object. <schema>.<element>.<qualifier>:<value>

        :param schema: The schema of the metadata field, for example dc, dspace, local, ...
        :param element: The element of the field.
        :param qualifier: The qualifier of the field. If None, no qualifier will be used.
        :param value: The value stored in the metadata field.
        :param language: Optional language parameter for a metadata field.
        """
        self.schema = schema
        self.element = element
        self.qualifier = qualifier if qualifier is not None else ''
        self.value = value
        self.language = language if language != '' else None

    def __eq__(self, other):
        """
        Checks if to Metadata objects ar equal.

        :param other: The metadata object to compare to
        :return: True if the two objects are equal, False otherwise
        :raises TypeError: If the parameter other is not of Type Metadata.
        """
        if not isinstance(other, MetaData):
            raise TypeError(f'Can not use = between type(Metadata) and type({type(other)})')
        other: MetaData
        return self.get_tag() == other.get_tag() and self.value == other.value and self.language == other.language

    def __gt__(self, other):
        """
        Checks if this object is greater than "other".

        :param other: The object to compare to
        :return: True if this object is greater than the other.
        :raises TypeError: If the parameter other is not of Type Metadata.
        """
        if not isinstance(other, MetaData):
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return self.__str__() > other.__str__()

    def __lt__(self, other):
        """
        Checks if this object is lower than "other".

        :param other: The object to compare to
        :return: True if this object is lower than the other.
        :raises TypeError: If the parameter other is not of Type Metadata.
        """
        if not isinstance(other, MetaData):
            raise TypeError(f'Can not use < between type(Metadata) and type({type(other)})')
        other: MetaData
        return self.__str__() < other.__str__()

    def __ge__(self, other):
        """
        Checks if this object is greater or equally to "other".

        :param other: The object to compare to
        :return: True if this object is greater or equally to the other.
        :raises TypeError: If the parameter other is not of Type Metadata.
        """
        if not isinstance(other, MetaData):
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return self > other or self == other

    def __le__(self, other):
        """
        Checks if this object is lower or equally to "other".

        :param other: The object to compare to
        :return: True if this object is lower or equally tot the other.
        :raises TypeError: If the parameter other is not of Type Metadata.
        """
        if not isinstance(other, MetaData):
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return self < other or self == other

    def __str__(self):
        """
        Creates a string representation of this object.
        """
        return f'{self.get_tag()}:{self.value}' + (f'[{self.language}]' if self.language is not None else '')

    def is_field(self, other) -> bool:
        """
        Looks up, if the name (<schema>.<element>.<qualifier>) of two fields are identical.
        :param other: The MetaData object to compare it with.
        :return: True, if the names are identical
        :raise TypeError: If the tag is not in the correct schema.
        """
        if isinstance(other, MetaData):
            return self.get_tag() == other.get_tag() and self.language == other.language
        if isinstance(other, str):
            field = other.split('.')
            if len(field) == 3:
                return self.schema == field[0] and self.element == field[1] and self.qualifier == field[2]
            if len(field) == 2:
                return self.schema == field[0] and self.element == field[1] and self.qualifier == ''

            raise TypeError(f'Could not parse tag "{other}"')

        return False

    def add_value(self, value):
        """
        Adds a value to the metadata field, if it already has a value.
        :param value: The value to add.
        """
        if self.value is None:
            self.value = value
        elif isinstance(self.value, list):
            self.value.append(value)
        else:
            self.value = [self.value, value]

    def get_tag(self) -> str:
        """
        Creates the corresponding classical metadata tag, based on <schema>.<element>.<qualifier>
        :return: The tag as a string.
        """
        return f'{self.schema}.{self.element}.{self.qualifier}'.strip('.')

    def to_dict(self) -> dict:
        """
        Create a DSpace compatible json version of the metadata object,
        aka: {<tag>: [{"value": <value>, "language": <language>}]}

        :return: The json representation of the metadata object as dict object.
        """
        values = [self.value] if not isinstance(self.value, list) else self.value
        return {self.get_tag(): [
            {"value": v} if self.language is None else {"value": v, "language": self.language} for v in values]}


class MetaDataList(list):
    """
    A list of metadata fields. Provides all methods of a classic list, but only for MetaData objects. If an object is
    appended to the list. The MetaDataList checks first, if there is already a metadata field with this tag.
    """
    def __init__(self, iterable: list[MetaData]):
        """
        Creates a new object of MetaDataList
        """
        super().__init__(iterable)

    def __setitem__(self, index, item: MetaData):
        """
        Sets a new MetaData item on position <index>

        :param index: The index of the position.
        :param item: The MetaData item to add
        :raise TypeError: If type(item) is not MetaData.
        """
        if not isinstance(item, MetaData):
            raise TypeError('Only items from type MetaData can be added to this list.')
        super().__setitem__(index, item)

    def insert(self, index, item: MetaData):
        """
        Inserts an object before a specific index.
        """
        if not isinstance(item, MetaData):
            raise TypeError('Only items from type MetaData can be added to this list.')
        super().insert(index, item)

    def append(self, item: MetaData):
        """
        Appends a new object at the end of the MetaDataList. If the tag of the item already exists with same language,
        the value will be appended to the existing object.

        :param item: The object to add.
        :raise TypeError: If type(item) is not MetaData
        """
        if not isinstance(item, MetaData):
            raise TypeError('Only items from type MetaData can be added to this list.')
        for i, v in enumerate(self):
            if item.is_field(v):
                self[i].add_value(item.value)
                return
        super().append(item)

    def extend(self, other):
        """
        Expanding the list by adding objects from another MetaDataList.
        """
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            raise TypeError('The type of the other list must correspond to MetadataList')

    def __str__(self):
        """
        Converts the MetaDataList into a string object.
        """
        return ', '.join([str(i) for i in self])

    def __add__(self, other):
        """
        Adds another MetaDataList to this and returns the result. Aka ` + `.
        """
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
        lst = list(filter(lambda x: x.get_tag() == tag, self))
        return lst if len(lst) > 0 else None

    def get_schemas(self) -> set[str]:
        """
        Creates a list of used schemas in the metadata list.

        :return: A list of schema names a strings.
        """
        return {i.schema for i in self}

    def to_dict(self) -> dict:
        """
        Create a DSpace compatible json version of the MetadataList object,
        aka: [{<tag>: [{"value": <value>, "language": <language>}]}, ...]

        :return: The json representation of the MetadataList object as dict object.
        """
        metadata_json = {}
        for tag in self:
            md_json = tag.to_dict()
            if tag.get_tag() in metadata_json.keys():
                metadata_json[tag.get_tag()] += md_json[tag.get_tag()]
            else:
                metadata_json.update(md_json)
        return metadata_json
