class InvalidMetadataException(AttributeError):
    from dspyce.metadata import MetadataField
    invalid_metadata_fields: list[MetadataField]

class RestObjectNotFoundError(FileNotFoundError):
    """ DSpaceObject not found. """
    def __init__(self, *args, **kwargs):
        pass