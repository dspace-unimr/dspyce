import os
import re
import requests


class Bitstream:
    """
        A class for managing bitstream files in the DSpace context.
    """
    file_name: str
    """The name of the file."""
    path: str
    """The path, where the file can be found."""
    description: str
    """A possible description of the bitstream."""
    permissions: list[dict[str, str]]
    """Permission which group shall have access to this file."""
    show: bool
    """If the file should be accessible for users or only provides information for the item import."""
    bundle: any
    """The bundle where to store the file. The default is set to the variable DEFAULT_BUNDLE."""
    primary: bool
    """If the bitstream shall be the primary bitstream for the item."""
    uuid: str
    """A uuid if the Bitstream already exists in a DSpace-Instance."""

    def __init__(self, name: str, path: str, bundle: any = None, uuid: str = None, primary: bool = False):
        """
        Creates a new Bitstream object.
        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
        :param uuid: The uuid of the bitstream if existing.
        :param primary: Primary is used to specify the primary bitstream.
        """
        self.file_name = name
        self.path = path
        self.path += '/' if len(self.path) > 0 and self.path[-1] != '/' else ''
        self.permissions = []
        self.description = ''
        self.bundle = bundle
        self.uuid = uuid
        self.primary = primary

    def __str__(self):
        """
        Provides all information about the DSpace-Content file.

        :return: A SAF-ready information string which can be used for the content-file.
        """
        export_name = self.file_name
        if self.bundle is not None:
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
            Add access information to the Bitstream.

            :param rw: Access-type r-read, w-write.
            :param group_name: Group to which the access will be provided.
        """
        if rw not in ('r', 'w'):
            raise ValueError(f'Permission type must be "r" or "w". Got {rw} instead!')
        self.permissions.append({'type': rw, 'group': group_name})

    def get_bitstream_file(self, timeout: int = 30) -> bytes:
        """
        Returns the actual file as a TextIOWrapper object.

        :param timeout: The connection timeout for reading bitstreams from remote resources.
        """
        if re.search(r'^http(s)?://', self.path):
            return requests.get(self.path, timeout=timeout).content
        with open(self.path + self.file_name, 'rb') as f:
            return f.read()

    def save_bitstream(self, path: str, timeout: int = 30):
        """
        Saves the current bitstream to the given path.

        :param path: The path where the bitstream file is to be saved.
        :param timeout: The connection timeout for reading bitstreams from remote resources.
        :raises FileExistsError: if the file already exists in the given path.
        """
        if self.file_name in os.listdir(path):
            raise FileExistsError(f'The file "{self.file_name}" already exists in {path}')
        file = self.get_bitstream_file(timeout)
        if isinstance(file, str):
            file = file.encode('utf-8')
        with open(f'{path}/{self.file_name}', 'wb') as f:
            f.write(file)

    def __eq__(self, other):
        """
        Checks if two content files are equal based on their name and path (and possible uuid).
        
        :param other: The other object to compare with.
        :raises TypeError: if the type of "other" is not Bitstream
        """
        if not isinstance(other, Bitstream):
            raise TypeError(f'Can not compare Bitstream with type({type(other)})')
        return (self.file_name == other.file_name and
                self.path == other.path and
                ((self.uuid is None or other.uuid is None) or self.uuid == other.uuid))
