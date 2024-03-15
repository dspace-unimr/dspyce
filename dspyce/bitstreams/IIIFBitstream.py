import warnings
from io import BytesIO
from PIL import Image

from dspyce.bitstreams import Bitstream


class IIIFBitstream(Bitstream):
    """
        A class for managing iiif-specific content files in the saf-packages.
    """

    iiif: dict[str, str | int]
    """
        A dictionary containing the IIIF-specific information. The keys must be: 'label', 'toc', 'w', 'h'
    """

    def __init__(self, name: str, path: str, bundle: any = None, uuid: str = None, primary: bool = False):
        """
        Creates a new IIIF-Bitstream object.

        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
        :param uuid: The uuid of the bitstream if existing.
        :param primary: Primary is used to specify the primary bitstream.
        """
        super().__init__(name, path, bundle, uuid, primary)
        self.iiif = {}

    def __str__(self):
        """
        Provides all information about the DSpace IIIF-Content file.

        :return: A SAF-ready information string which can be used for the content-file.
        """
        export_name = super().__str__()
        if len(self.iiif.keys()) > 0:
            export_name += (f'\tiiif-label:{self.iiif["label"]}'
                            f'\tiiif-toc:{self.iiif["toc"]}'
                            f'\tiiif-width:{self.iiif["w"]}'
                            f'\tiiif-height:{self.iiif["h"]}')
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
        img = Image.open(BytesIO(self.get_bitstream_file()))
        width, height = img.size
        if w != 0 and w < width:
            scale = int(width/w)
            super().file = img.reduce(scale).tobytes()
        img.close()
        self.iiif = {'label': label, 'toc': toc, 'w': width, 'h': height}
