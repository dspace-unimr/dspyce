from PIL import Image


class ContentFile:
    """
        A class for managing content files in the saf-packages.
    """
    content_type: str
    file_name: str
    path: str
    file: bytes | str
    description: str
    permissions: list[dict]
    iiif: dict
    show: bool

    def __init__(self, content_type: str, name: str, path: str, content: str | bytes = '', show: bool = True):
        """
        Creates a new ContentFile object.

        :param content_type: The type of content file. Must be one off: ('relations', 'licenses', 'images', 'contents',
        'handle', 'other')
        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param content: The content of the file, if it shouldn't be loaded from the system.
        :param show: If the bitstream should be listed in the saf-contentfile. Default: True - if the type is relations
        or handle the default is False.
        """
        types = ('relations', 'licenses', 'images', 'contents', 'handle', 'other')
        if content_type not in types:
            raise KeyError(f'Content-Type {content_type} does not exist. Value must be one of {types}')
        self.content_type = content_type
        self.file_name = name
        self.path = path
        if len(self.path) > 0 and self.path[-1] != '/':
            self.path += '/'
        if content_type == 'relations':
            self.file = content
        elif content != '':
            self.file = content
        else:
            with open(self.path + self.file_name, 'rb') as f:
                self.file = f.read()

        self.permissions = []
        self.iiif = {}
        self.description = ''
        self.show = show
        if self.content_type in ('relations', 'handle'):
            self.show = False

    def __str__(self):
        export_name = self.file_name
        if self.description != '':
            export_name += '\tdescription:%s' % self.description
        if len(self.permissions) > 0:
            for p in self.permissions:
                export_name += '\tpermissions:-%s \'%s\'' % (p['type'], p['group'])
        if len(self.iiif.keys()) > 0:
            export_name += '\tiiif-label:{}\tiiif-toc:{}\tiiif-width:{}\tiiif-height:{}'.format(
                self.iiif['label'], self.iiif['toc'], self.iiif['w'], self.iiif['h'])
        return export_name

    def add_description(self, description):
        """
            Creates a description to the content-file.

            :param description: String which provides the description..
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

    def add_iiif(self, label: str, toc: str, w: int = 0):
        """
            Add, if necessary IIIF-information for the bitstream.

            :param label: is the label that will be used for the image in the viewer.
            :param toc: is the label that will be used for a table of contents entry in the viewer.
            :param w: is the image width to reduce it. Default 0
        """
        img = Image.open(self.path+self.file_name)
        width, height = img.size
        if w != 0 and w < width:
            scale = int(width/w)
            self.file = img.reduce(scale).tobytes()
        img.close()
        self.iiif = {'label': label, 'toc': toc, 'w': width, 'h': height}

    def create_file(self, path: str):
        """
            Creates the need bitstream-file in the archive-directory based on the path information.

            :param path: The path, where the bitstream shall be saved.
        """
        with open(path+self.file_name, 'wb' if type(self.file) is bytes else 'w') as f:
            f.write(self.file)
