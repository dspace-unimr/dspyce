from MetaData import MetaDataList, MetaData


class DSpaceObject:
    """
    The class DSpaceObject represents an Object in a DSpace repository, such as Items, Collections, Communities.
    """

    metadata: MetaDataList
    """The metadata provided for the object."""

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

