from ..bitstreams.Bundle import Bundle


class ContentFile:
    """
        A class for managing content files in the saf-packages.
    """
    content_type: str
    """
    The type of the content file. Must be one off: ('relations', 'licenses', 'images', 'contents',
    'handle', 'other')
    """
    file_name: str
    """The name of the file."""
    path: str
    """The path, where the file can be found."""
    file: bytes | str | None
    """The file itself, if is should not be loaded from file-system."""
    description: str
    """A possible description of the bitstream."""
    permissions: list[dict[str, str]]
    """Permission which group shall have access to this file."""
    show: bool
    """If the file should be accessible for users or only provides information for the item import."""
    bundle: Bundle
    """The bundle where to store the file. The default is set to the variable DEFAULT_BUNDLE."""
    primary: bool
    """If the bitstream shall be the primary bitstream for the item."""
    uuid: str
    """A uuid if the ContentFile already exists in a DSpace-Instance."""

    def __init__(self, content_type: str, name: str, path: str, content: str | bytes = '',
                 bundle: str | Bundle = Bundle.DEFAULT_BUNDLE, primary: bool = False, show: bool = True):
        """
        Creates a new ContentFile object.

        :param content_type: The type of content file. Must be one off: ('relations', 'licenses', 'images', 'contents',
        'handle', 'other')
        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param content: The content of the file, if it shouldn't be loaded from the system.
        :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
        :param primary: Primary is used to specify the primary bitstream.
        :param show: If the bitstream should be listed in the saf-content file. Default: True - if the type is relations
        or handle the default is False.
        """
        types = ('relations', 'licenses', 'images', 'contents', 'handle', 'collections', 'other')
        if content_type not in types:
            raise KeyError(f'Content-Type {content_type} does not exist. Value must be one of {types}')
        self.content_type = content_type
        self.file_name = name
        self.path = path
        self.path += '/' if len(self.path) > 0 and self.path[-1] != '/' else ''
        if content_type == 'relations':
            self.file = content
        elif content != '':
            self.file = content
        else:
            self.file = None
        self.permissions = []
        self.description = ''
        bundle = bundle if str(bundle) != '' else Bundle.DEFAULT_BUNDLE
        if type(bundle) is not Bundle:
            self.bundle = Bundle(name=bundle)
        else:
            self.bundle = bundle

        self.primary = primary
        self.show = show
        if self.content_type in ('relations', 'handle', 'collections'):
            self.show = False

    def __str__(self):
        """
        Provides all information about the DSpace-Content file.

        :return: A SAF-ready information string which can be used for the content-file.
        """
        export_name = self.file_name
        if self.bundle.name != '' and self.bundle.name != Bundle.DEFAULT_BUNDLE:
            export_name += f'\tbundle:{self.bundle.name}'
        if self.description != '':
            export_name += f'\tdescription:{self.description}'
        if len(self.permissions) > 0:
            for p in self.permissions:
                export_name += f'\tpermissions:-{p["type"]} \'{p["group"]}\''
        if self.primary:
            export_name += '\tprimary:true'
        return export_name

    def add_description(self, description):
        """
            Creates a description to the content-file.

            :param description: String which provides the description.
        """
        self.description = description

    def add_permission(self, rw: str, group_name: str):
        """
            Add access information to the ContentFile.

            :param rw: Access-type r-read, w-write.
            :param group_name: Group to which the access will be provided.
        """
        if rw not in ('r', 'w'):
            raise ValueError(f'Permission type must be "r" or "w". Got {rw} instead!')
        self.permissions.append({'type': rw, 'group': group_name})
