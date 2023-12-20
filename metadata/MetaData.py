
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
        if type(other) is not MetaData:
            raise TypeError(f'Can not use = between type(Metadata) and type({type(other)})')
        other: MetaData
        return self.get_tag() == other.get_tag() and self.value == other.value and self.language == other.language

    def __gt__(self, other):
        if type(other) is not MetaData:
            raise TypeError(f'Can not use > between type(Metadata) and type({type(other)})')
        other: MetaData
        return self.__str__() > other.__str__()

    def __lt__(self, other):
        if type(other) is not MetaData:
            raise TypeError(f'Can not use < between type(Metadata) and type({type(other)})')
        other: MetaData
        return self.__str__() < other.__str__()

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
        return f'{self.get_tag()}:{self.value}'

    def is_field(self, other) -> bool:
        """
        Looks up, if the name (<schema>.<element>.<qualifier>) of two fields are identical.
        :param other: The MetaData object to compare it with.
        :return: True, if the names are identical
        """
        if isinstance(other, MetaData):
            return (self.get_tag() == other.get_tag() and self.language == other.language)
        elif isinstance(other, str):
            field = other.split('.')
            if len(field) == 3:
                return self.schema == field[0] and self.element == field[1] and self.qualifier == field[2]
            elif len(field) == 2:
                return self.schema == field[0] and self.element == field[1] and self.qualifier == ''
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

    def get_tag(self) -> str:
        """
        Creates the corresponding classical metadata tag, based on <schema>.<element>.<qualifier>
        :return: The tag as a string.
        """
        return f'{self.schema}.{self.element}.{self.qualifier}'.strip('.')
