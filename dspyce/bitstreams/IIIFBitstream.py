import warnings
from io import BytesIO

from PIL import Image

from dspyce.bitstreams import Bitstream


class IIIFBitstream(Bitstream):
    """
        A class for managing iiif-specific content files in the saf-packages.
    """

    def __init__(self, name: str, path: str, bundle: any = None, uuid: str = None, primary: bool = False,
                 size_bytes: int = None, check_sum: str = None):
        """
        Creates a new IIIF-Bitstream object.

        :param name: The name of the bitstream.
        :param path: The path, where the file is currently stored.
        :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
        :param uuid: The uuid of the bitstream if existing.
        :param primary: Primary is used to specify the primary bitstream.
        :param size_bytes: The size of the bitstream in bytes.
        :param check_sum: The checksum of the bitstream.
        """
        super().__init__(name, path, bundle, uuid, primary, size_bytes, check_sum)

    def __str__(self):
        """
        Provides all information about the DSpace IIIF-Content file.

        :return: A SAF-ready information string which can be used for the content-file.
        """
        export_name = super().__str__()
        if len(self.iiif.keys()) > 0:
            export_name += (f'\tiiif-label:{self.get_iiif_label()}'
                            f'\tiiif-toc:{self.get_iiif_toc()}'
                            f'\tiiif-width:{self.get_first_metadata_value('iiif.image.width')}'
                            f'\tiiif-height:{self.get_first_metadata_value('iiif.image.height')}')
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
        self.add_metadata('iiif.label', label)
        self.add_metadata('iiif.toc', toc)
        self.add_metadata('iiif.image.width', str(width))
        self.add_metadata('iiif.image.height', str(height))

    def get_iiif_label(self) -> str | None:
        """
        Returns the label of the IIIF bitstream.
        """
        return self.get_first_metadata_value('iiif.label')

    def get_iiif_toc(self) -> str | None:
        """
        Returns the toc label of the IIIF bitstream.
        """
        return self.get_first_metadata_value('iiif.toc')

    def get_bitstream_size(self) -> tuple[float, float] | None:
        """
        Returns the size (width, height) of a given bitstream as a tuple of float values.
        """
        if (self.get_first_metadata_value('iiif.image.width') is not None and
            self.get_first_metadata_value('iiif.image.height') is not None):
            return (float(self.get_first_metadata_value('iiif.image.width')),
                    float(self.get_first_metadata_value('iiif.image.height')))
        return None
