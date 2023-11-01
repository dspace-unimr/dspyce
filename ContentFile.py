import os
from typing import List
from PIL import Image, ImageOps


class ContentFile:
    """
        Eine Klasse zum Verwalten eines Content-Files des DSPACE-Ordners.
    """
    content_type: str
    file_name: str
    path: str
    file: (bytes, str)
    description: str
    permissions: List[dict]
    iiif: dict
    show: bool
    server: str

    def __init__(self, content_type: str, name: str, path: str, content: (str | bytes) = '', show: bool = True,
                 server: str = ''):
        types = ('relations', 'licenses', 'images', 'contents', 'handle', 'other')
        if content_type not in types:
            raise KeyError('Content-Type %s doesn\'t exist. Value must be from %s' % (content_type, types))
        self.content_type = content_type
        self.file_name = name
        self.path = path
        if len(self.path) > 0 and self.path[-1] != '/':
            self.path += '/'
        self.server = server
        if content_type == 'relations':
            self.file = content
        elif content != '':
            self.file = content
        else:
            if server == '':
                with open(self.path + self.file_name, 'rb') as f:
                    self.file = f.read()
            else:
                try:
                    os.mkdir('tmp')
                except FileExistsError:
                    pass
                os.system(f'scp {server}:{path + name} ./tmp/')
                if server == 'vhrz675':
                    im = ImageOps.invert(Image.open('./tmp/' + name))
                    os.remove(f'./tmp/{name}')
                    im.save('./tmp/' + name)
                    im.close()
                print(f'Server: "{server}"')
                with open('./tmp/' + name, 'rb') as f:
                    self.file = f.read()
                self.path = './tmp/'

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
            Fügt eine Beschreibung für das ContentFile hinzu.

            :param description: String der die Beschreibung enthält.
        """
        self.description = description

    def add_permission(self, rw: str, group_name: str):
        """
            Fügt Zugriffs-Informationen zu einem ContentFile hinzu.

            :param rw: Art des Zugriffs r-read, w-write.
            :param group_name: Gruppe, der der Zugriff gewährt wird.
        """
        if rw not in ('r', 'w'):
            raise ValueError('Permission type must be "r" or "w". Got %s instead!' % rw)
        self.permissions.append({'type': rw, 'group': group_name})

    def add_iiif(self, label: str, toc: str, w: int = 0):
        """
            Fügt, wenn nötig IIIF-Informationen dem Bitstream hinzu.

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
            Erstellt das entsprechende bitstream-file.

            :param path: Der Pfad unter dem das entsprechende Dokument gespeichert werden soll.
        """
        with open(path+self.file_name, 'wb' if type(self.file) is bytes else 'w') as f:
            f.write(self.file)
        if self.server != '':
            try:
                os.remove(f'./tmp/{self.file_name}')
            except FileNotFoundError:
                pass
