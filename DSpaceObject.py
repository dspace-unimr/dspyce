from .metadata import MetaDataList, MetaData


def parse_metadata_label(label: str) -> tuple[str, str, str | None]:
    """
    Parses a dspace metadata label string from the format <schema>.<element>.<qualifier>

    >>> parse_metadata_label('dc.type')
    ('dc', 'type', None)
    >>> parse_metadata_label('dspace.entity.type')
    ('dspace, 'entity', 'type')

    :param label: The metadata label to parse.
    :return: A tuple containing prefix, element and qualifier of a label.
    """
    label = label.split('.')
    if len(label) == 2:
        return label[0], label[1], None
    elif len(label) == 3:
        return label[0], label[1], label[2]
    else:
        raise KeyError(f'Could not parse dspace-metadata label "{label}"')


class DSpaceObject:
    """
    The class DSpaceObject represents an Object in a DSpace repository, such as Items, Collections, Communities.
    """

    uuid: str
    """The uuid of the DSpaceObject"""
    name: str
    """The name of the DSpaceObject, if existing"""
    handle: str
    """The handle of the Object"""
    metadata: MetaDataList
    """The metadata provided for the object."""

    def __init__(self, uuid: str = '', handle: str = '', name: str = ''):
        """
        Creates a new object of the class DSpaceObject

        :param uuid: The uuid of the DSpaceObject. Default is ''
        :param handle: The handle of the DSpaceObject. Default is ''
        """
        self.uuid = uuid
        self.handle = handle
        self.name = name
        self.metadata = MetaDataList([])
        if name != '':
            self.add_dc_value('title', None, name)

    def add_dc_value(self, element: str, qualifier: str | None, value: str, language: str = None):
        """
        Creates a new dc- metadata field with the given value.

        :param element: Type of the metadata-field. For example 'title'.
        :param qualifier: The qualifier of the field.
        :param value: The value of the metadata-field.
        :param language: The language of the metadata field. Default: None.
        """
        self.add_metadata('dc', element, qualifier, value, language)

    def add_metadata(self, prefix: str, element: str, qualifier: str | None, value: str, language: str = None):
        """
        Creates a new metadata field with the given value. The schema is specified through the prefix parameter.

        :param element: Type of the metadata-field. For example 'title'.
        :param value: The value of the metadata-field.
        :param prefix: The prefix of the schema, which should be used.
        :param qualifier: The qualifier of the field.
        :param language: The language of the metadata field.
        """
        self.metadata.append(MetaData(prefix, element, qualifier, value, language))

    def get_dspace_object_type(self) -> str:
        """
        This Function serves mainly to be overwritten by subclasses to get the type of DSpaceObject.
        """
        pass

    def get_identifier(self) -> str:
        """
        Returns the identifier of this object. Preferably this will be the uuid, but if this, does not exist, it uses
        the handle.
        :return: The identifier as a string.
        """
        if self.uuid != '':
            return self.uuid
        elif self.handle != '':
            return self.handle
        else:
            return ''

    def __eq__(self, other):
        if self.uuid == '' and other.uuid == '':
            raise ValueError('Can not compare objects without a uuid')
        return self.uuid == other.uuid

    def __str__(self):
        self.metadata.sort()
        data = '\n'.join(f'\t{str(m)}' for m in self.metadata)
        return f'DSpace object with the uuid {self.uuid}:\n{data}'

    def to_dict(self) -> dict:
        """
            Converts the curent item object to a dictionary object containing all available metadata.
        """
        dict_obj = {'uuid': self.uuid, 'handle': self.handle, 'name': self.name}
        for m in self.metadata:
            m: MetaData
            tag = m.get_tag()
            value = m.value
            if m.language is not None:
                value = {m.language: value}
                if tag in dict_obj.keys():
                    value.update(dict_obj[tag] if type(dict_obj[tag]) is dict else {'': dict_obj[tag]})
            dict_obj[tag] = value
        return dict_obj

    def get_metadata_values(self, tag: str) -> list:
        """
        Retrieves the metadata values of a specific tag as a list.

        :param tag: The metadata tag: prefix.element.qualifier
        :return: The values as a list.
        """
        values = self.metadata.get(tag)
        return values if isinstance(values, list) or values is None else [values]
