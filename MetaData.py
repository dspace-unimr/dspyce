
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
        self.language = language

    def __eq__(self, other):
        if type(other) is not MetaData:
            raise TypeError(f'Can not use = between type(Metadata) and type({type(other)})')
        other: MetaData
        return (self.schema == other.schema and self.element == other.element and self.qualifier == other.qualifier
                and self.value == other.value)

    def __gt__(self, other):
        if type(other) is not MetaData:
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return (self.schema > other.schema or (self.schema == other.schema and self.element > other.element) or
                (self.schema == other.schema and self.element == other.element and self.qualifier > other.qualifier) or
                (self.schema == other.schema and self.element == other.element and self.qualifier == other.qualifier and
                 self.value > other.value))

    def __ge__(self, other):
        if type(other) is not MetaData:
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return self > other or self == other

    def __le__(self, other):
        if type(other) is not MetaData:
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return self < other or self == other

    def __str__(self):
        return f'{self.schema}.{self.element}{"." + self.qualifier if self.qualifier != "" else ""}:{self.value}'

    def is_field(self, other) -> bool:
        """
        Looks up, if the name (<schema>.<element>.<qualifier>) of two fields are identical.
        :param other: The MetaData object to compare it with.
        :return: True, if the names are identical
        """
        if isinstance(other, MetaData):
            return (self.schema == other.schema and self.element == other.element and self.qualifier == other.qualifier and
                    self.language == other.language)
        elif isinstance(other, str):
            field = other.split('.')
            if len(field) == 3:
                return self.schema == field[0] and self.element == [1] and self.qualifier == field[2]
            elif len(field) == 2:
                return self.schema == field[0] and self.element == [1] and self.qualifier is None
            else:
                raise TypeError(f'Could not parse tag "{other}"')
        else:
            return False

    def add_value(self, value):
        """
        Adds a value to the metadata field, if it already has a value.
        :param value: The value to add.
        """
        if self.value is None:
            self.value = value
        elif type(self.value) is list:
            self.value.append(value)
        else:
            self.value = [self.value, value]


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
