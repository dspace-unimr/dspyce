import re


class MetaDataValue:
    """
    This class represents a metadata field for a DSpace object. Containing information about the schema, element,
    qualifier and value.
    """
    language: str | None
    """The language of the metadata value. For example 'en' for English."""
    value: str | int | float | bool
    """The actual metadata value."""

    def __init__(self, value: str | int | float | bool, language: str = None):
        """
        Creates a new MetaDataValue object.

        :param value: The value stored in the metadata field.
        :param language: Optional language parameter for a metadata field.
        """
        self.value = value
        self.language = language if language != '' else None

    def __eq__(self, other):
        """
        Checks if to Metadata objects ar equal.

        :param other: The metadata object to compare to
        :return: True if the two objects are equal, False otherwise
        :raises TypeError: If the parameter other is not of Type Metadata.
        """
        if not isinstance(other, MetaDataValue):
            raise TypeError(f'Can not use = between type(MetadataValue) and type({type(other)})')
        other: MetaDataValue
        return (isinstance(self.value, type(other.value)) and
                self.value == other.value and self.language == other.language)

    def __str__(self):
        """
        Creates a string representation of this object.
        """
        return (f'{self.language}:\t' if self.language else '') + str(self.value)

    def set_value(self, value):
        """
        Adds a value to the metadata field, if it already has a value, the old value will be overwritten.
        :param value: The value to add.
        """
        self.value = value

    def __iter__(self):
        """
        Returns a dictionary representation of this object.
        """
        yield 'value', self.value
        if self.language is not None:
            yield 'language', self.language


class MetaData(dict):
    """
    A dict of metadata fields using the following format: "<tag>": list(MetaDataValue)
    """

    @staticmethod
    def is_valid_tag(tag) -> bool:
        """
        Checks if the given tag is valid using RegEx.

        :param tag: The tag to check.
        :return: True if the tag is valid, False otherwise.
        """
        if re.search(r'^[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)?$', tag):
            return True
        return False

    def __setitem__(self, key: str, value: MetaDataValue | list[MetaDataValue]):
        """
        Adds a value to the metadata field defined by key. If the metadata field already exists, the value will be
        appended. If value is a list of MetaDataValues, the values will be replaced with the new value list.

        :param key: The key of the metadata field to add (must be in the correct format).
        :param value: The value to add. If this is of type list, the new list of MetadataValues will replace the old one
        :raises TypeError: If the parameter value is not of type MetaDataValue.
        :raises KeyError: If the parameter key has not a valid format.
        """
        if not isinstance(value, MetaDataValue) and not isinstance(value, list):
            raise TypeError(f'The value must be of type MetaDataValue, but found {type(value)}')
        if not MetaData.is_valid_tag(key):
            raise KeyError(f'The key "{key}" is not a valid metadata key.')
        if isinstance(value, list):
            for v in value:
                if not isinstance(v, MetaDataValue):
                    raise TypeError(f'All values must be of type MetaDataValue, but found {type(value)}')
            super().__setitem__(key, value)
        else:
            if key not in self.keys():
                super().__setitem__(key, [value])
            else:
                super().__getitem__(key).append(value)

    def get_schemas(self) -> set[str]:
        """
        Creates a list of used schemas in the metadata list.

        :return: A list of schema names a strings.
        """
        return {k.split('.')[0] for k in self.keys()}

    def __getitem__(self, item) -> list[MetaDataValue]:
        return super().__getitem__(item)

    def get(self, key, default=None) -> list[MetaDataValue]:
        return super().get(key, default)

    def __str__(self):
        """
        Creates a string representation of the Metadata object.
        """
        return '\n'.join([f'{k}:\n' + '\n'.join([f'\t{v}' for v in self.get(k)]) for k in self.keys()])

    def get_by_schema(self, schema: str):
        """
        Returns a sub-dictionary only including metadata fields from the given schema.

        :param schema: The schema name.
        :return: A sub-dictionary of the given schema.
        :raises KeyError: If the given schema does not have any metadata fields.
        """
        if schema not in self.get_schemas():
            raise KeyError(f'The schema "{schema}" is not used.')
        return MetaData({k: self.__getitem__(k) for k in filter(lambda x: x.split('.')[0] == schema, self.keys())})
