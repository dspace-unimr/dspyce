from ContentFile import ContentFile, DEFAULT_BUNDLE
from PIL import Image
import warnings


class IIIFContent(ContentFile):
    """
        A class for managing iiif-specific content files in the saf-packages.
    """

    iiif: dict[str, str | int]
    """
        A dictonary containing the IIIF-specific information. The keys must be: 'label', 'toc', 'w', 'h'
    """

    def __init__(self, content_type: str, name: str, path: str, content: str | bytes = '', bundle: str = DEFAULT_BUNDLE,
                 primary: bool = False, show: bool = True):
        """
        Creates a new IIIF-ContentFile object.

        :param content_type: The type of content file. Must be one of: 'images'
        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param content: The content of the file, if it shouldn't be loaded from the system.
        :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
        :param primary: Primary is used to specify the primary bitstream.
        :param show: If the bitstream should be listed in the saf-content file. Default: True - if the type is relations
        or handle the default is False.
        """
        if content_type != 'images':
            raise TypeError('If you use a IIIFContentfile object to create saf content files, the content_type must be'
                            '"images", if you want another content type, please use the super-class `ContentFile`.'
                            f'\n\t"{content_type}" is not allowed here!')
        super().__init__(content_type, name, path, content, bundle, primary, show)
        self.iiif = {}

    def __str__(self):
        """
        Provides all information about the DSpace IIIF-Content file.

        :return: A SAF-ready information string which can be used for the content-file.
        """
        export_name = str(super)
        if len(self.iiif.keys()) > 0:
            export_name += '\tiiif-label:{}\tiiif-toc:{}\tiiif-width:{}\tiiif-height:{}'.format(
                self.iiif['label'], self.iiif['toc'], self.iiif['w'], self.iiif['h'])
        else:
            warnings.warn('You are about to generate information of IIIF-specific DSpace bitstream, without providing'
                          'IIIF-specific information. Are you sure, you want to do this?')
        return export_name

    def add_iiif(self, label: str, toc: str, w: int = 0):
        """
            Add  IIIF-information for the bitstream.

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
