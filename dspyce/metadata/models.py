import logging
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
    authority: str | None = None
    """A possible authority value of the metadata value."""
    confidence: int = -1
    """The confidence level of the metadata value."""

    def __init__(self, value: str | int | float | bool, language: str = None, authority: str = None, confidence : int = -1):
        """
        Creates a new MetaDataValue object.

        :param value: The value stored in the metadata field.
        :param language: Optional language parameter for a metadata field.
        :param authority: Optional authority parameter for a metadata field.
        :param confidence: Optional confidence level for a metadata field.
        """
        self.value = value
        self.language = language if language != '' else None
        self.authority = authority
        self.confidence = confidence

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
        if self.authority is not None:
            yield 'authority', self.authority
        if self.confidence != -1:
            yield 'confidence', self.confidence


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
                self.__getitem__(key).append(value)

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

    def to_dict(self):
        """
        Returns the metadata including all values as a rest-compatible dictionary.
        """
        return {k: list(map(lambda x: dict(x), self.get(k))) for k in self.keys()}


class MetadataSchema:
    id: int
    """The ID of the metadata schema."""
    prefix: str
    """The prefix of the metadata schema, aka dc, dc-terms, ..."""
    namespace: str
    """An url to the namespace of the schema."""

    def __init__(self, prefix: str, namespace: str, id: int = None):
        """
        Creates a new object of the  MetadataSchema class.
        :param prefix: The prefix of the schema.
        :param namespace: The namespace of the schema.
        :param id: The id of the schema, optional.
        """
        self.prefix = prefix
        self.namespace = namespace
        self.id = id

    @staticmethod
    def get_schemas_from_rest(rest_api):
        """
        Retrieves a metadata schema by its id from the given rest API.
        :param rest_api: The rest API object to use.
        """
        """
        Retrieves all sub communities from the current community.
        :param rest_api: The rest API object to use.
        :param in_place: If True, the returned object will be placed into the current community.
        :return: A list of sub communities if in_place i False, None otherwise.
        """
        url = f'/core/metadataschemas'
        objs = rest_api.get_paginated_objects(url, 'metadataschemas')
        logging.debug('Retrieved %i metadataschemas.', len(objs))
        return [MetadataSchema(i['prefix'], i['namespace'], i['id']) for i in objs]

    @staticmethod
    def get_schema_from_rest(rest_api, id: int):
        """
        Retrieves a metadata schema by its id from the given rest API.
        :param rest_api: The rest API object to use.
        :param id: The id of the schema to retrieve.
        """
        url = f'/core/metadataschemas/{id}'
        obj = rest_api.get_api(url)
        if obj is None:
            logging.error('Could not retrieve metadata schema with id %i.', id)
            return None
        schema_obj = MetadataSchema(obj['prefix'], obj['namespace'], obj['id'])
        logging.debug('Retrieved metadataschema with prefix.', schema_obj.prefix)
        return schema_obj

class MetadataField:
    id: int
    """The id of the metadata field."""
    schema: MetadataSchema
    """The MetadataSchema of the metadata field."""
    element: str
    """The name of the metadata field."""
    qualifier: str | None
    """The qualifier of the metadata field."""
    scope_note: str | None
    """The scope note of the metadata field."""

    def __init__(self, schema: MetadataSchema, element: str, qualifier: str = None, scope_note: str = None, id: int = None):
        """
        Creates a new metadata field object.
        :param element: The name of the metadata field.
        :param qualifier: The qualifier of the metadata field.
        :param scope_note: The scope note of the metadata field.
        :param id: The id of the metadata field, optional.
        """
        self.schema = schema
        self.element = element
        self.qualifier = qualifier
        self.scope_note = scope_note
        self.id = id

    def update_schema_from_rest(self, rest_api):
        """
        Updates the schema information from the given rest API object based on the ID of the current metadata field.
        :param rest_api: The rest API object to use.
        """
        url = f'/core/metadatafields/{id}/schema'
        obj = rest_api.get_api(url)
        self.schema = MetadataSchema(obj['prefix'], obj['namespace'], obj['id'])

    @staticmethod
    def get_metadata_field_from_rest(rest_api, id: int):
        """
        Retrieves a specific metadata field from the given rest API.
        :param rest_api: The rest API object to use.
        :param id: The id of the metadata field to retrieve.
        :return: The new MetadataField object.
        """
        url = f'/core/metadatafields/{id}'
        obj = rest_api.get_api(url)
        if obj is None:
            logging.error('Could not retrieve metadata field with id %i.', id)
            return None
        schema_obj = None
        if obj.get('_embedded') is not None and obj['_embedded'].get('schema') is not None:
            schema_obj = MetadataSchema(obj['_embedded']['schema']['prefix'],
                                        obj['_embedded']['schema']['namespace'],
                                        obj['_embedded']['schema']['id'])
        field_obj = MetadataField(schema_obj, obj['element'], obj.get('qualifier'), obj.get('scope_note'), obj['id'])
        if schema_obj is None:
            field_obj.update_schema_from_rest(rest_api)
        logging.debug('Retrieved metadata field "%s".', str(field_obj))
        return field_obj

    def __str__(self):
        """Creates string representation of the current MetadataField object."""
        return f'{self.schema.prefix}.{self.element}' + (f'.{self.qualifier}' if self.qualifier is not None else '')

