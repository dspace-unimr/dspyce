from .metadata import MetaDataList, MetaData


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

    def __eq__(self, other):
        if self.uuid == '' and other.uuid == '':
            raise ValueError('Can not compare objects without a uuid')
        return self.uuid == other.uuid

    def __str__(self):
        self.metadata.sort()
        data = '\n'.join(f'\t{str(m)}' for m in self.metadata)
        return f'DSpace object with the uuid {self.uuid}:\n{data}'


def parse_metadata_label(label: str) -> tuple[str, str, str | None]:
    """
    Parses a dspace metadata label string from the format <schema>.<element>.<qualifier>
    :param label:
    :return:
    """
    label = label.split('.')
    if len(label) == 2:
        return label[0], label[1], None
    elif len(label) == 3:
        return label[0], label[1], label[2]
    else:
        raise KeyError(f'Could not parse dspace-metadata label "{label}"')
