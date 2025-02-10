import os
import re
import requests

from dspyce.DSpaceObject import DSpaceObject


class Bitstream(DSpaceObject):
    """
        A class for managing bitstream files in the DSpace context.
    """
    file_name: str
    """The name of the file."""
    path: str
    """The path, where the file can be found."""
    permissions: list[dict[str, str]]
    """Permission which group shall have access to this file."""
    show: bool
    """If the file should be accessible for users or only provides information for the item import."""
    bundle: any
    """The bundle where to store the file. The default is set to the variable DEFAULT_BUNDLE."""
    primary: bool
    """If the bitstream shall be the primary bitstream for the item."""
    size_bytes: int
    """The size of the Bitstream in bytes."""
    check_sum: str
    """The checksum of the Bitstream."""

    def __init__(self, name: str, path: str, bundle: any = None, uuid: str = None, primary: bool = False,
                 size_bytes: int = None, check_sum: str = None):
        """
        Creates a new Bitstream object.
        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
        :param uuid: The uuid of the bitstream if existing.
        :param primary: Primary is used to specify the primary bitstream.
        :param size_bytes: The size of the bitstream in bytes.
        :param check_sum: The checksum of the bitstream.
        """
        self.file_name = name
        self.path = path
        self.path += '/' if len(self.path) > 0 and self.path[-1] != '/' else ''
        self.permissions = []
        self.bundle = bundle
        self.primary = primary
        self.size_bytes = size_bytes
        self.check_sum = check_sum
        super().__init__(uuid, '', name)
        if name != '':
            self.add_metadata('dc.title', name)

    def __str__(self):
        """
        Provides all information about the DSpace-Content file.

        :return: A SAF-ready information string which can be used for the content-file.
        """
        export_name = self.file_name
        if self.bundle is not None:
            export_name += f'\tbundle:{self.bundle.name}'
        if self.get_description() is not None:
            export_name += f'\tdescription:{self.get_description()}'
        if len(self.permissions) > 0:
            for p in self.permissions:
                export_name += f'\tpermissions:-{p["type"]} \'{p["group"]}\''
        if self.primary:
            export_name += '\tprimary:true'
        return export_name

    def get_description(self):
        """
        Returns the current description of the current bitstream.
        """
        return self.get_first_metadata_value('dc.description')

    def add_description(self, description: str, language: str = None):
        """
            Creates a description to the content-file.

            :param description: String which provides the description.
            :param language: The language of the description.
        """
        self.add_metadata('dc.description', description, language)

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
        if self.is_remote_resource():
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

    def get_dspace_object_type(self) -> str:
        """
        Return the DSpaceObject type for the bitstream object, aka "Bitstream"
        """
        return 'Bitstream'

    def get_identifier(self) -> str | None:
        """
        Overwrites the standard DSpace-Object get_identifier method: only returns uuid for bitstreams (no handles
        allowed)
        """
        return self.uuid

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the bitstream object.
        """
        obj_dict = super().to_dict()
        if self.bundle is not None and self.bundle.name != '':
            obj_dict['bundleName'] = self.bundle.name
        return obj_dict

    def set_size(self, size: int = None):
        """
        Sets the size of the bitstream. If parameter size is None, this method is calculating the size of the Bitstream.
        :param size: The size of the bitstream.
        """
        if size is None:
            if self.is_remote_resource():
                headers = requests.head(self.path).headers
                if 'Content-Length' in headers:
                    self.size_bytes = int(headers['Content-Length'])
                else:
                    raise requests.exceptions.InvalidHeader('Did not get "Content-Length key in the header."')
            else:
                self.size_bytes = os.path.getsize(self.path)
        else:
            self.size_bytes = size

    def is_remote_resource(self) -> bool:
        """
        Checks if the resources should be retrieved from an url.
        :return: True if the path starts with http(s)?://
        """
        return re.search(r'^http(s)?://', self.path) is not None
