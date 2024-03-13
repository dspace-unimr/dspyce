# dspyce.bitstreams
## Package contents:
1. [Bundle](#bundle)
2. [Bitstream](#bitstream)
3. [IIIFBitstream](#iiifbitstream)
## Package documentation
### Bundle
```
class Bundle(builtins.object)
 |  Bundle(name: str = 'ORIGINAL', description: str = '', uuid: str = None)
 |  
 |  The class Bundle represents a bundle in the DSpace context. I can contain several bitstreams.
 |  
 |  Methods defined here:
 |  
 |  __eq__(self, other) -> bool
 |      Check if two bundle objects are equal
 |      
 |      :param other: The other bundle object to compare with.
 |      :return: True, if the two bundles have the same name.
 |  
 |  __init__(self, name: str = 'ORIGINAL', description: str = '', uuid: str = None)
 |      Creates a new bundle object.
 |      
 |      :param name: The bundle name.
 |      :param description: A description if existing.
 |      :param uuid: The uuid of the bundle, if known.
 |  
 |  __str__(self)
 |      Return str(self).
```
### Bitstream
```
class Bitstream(builtins.object)
 |  Bitstream(content_type: str, name: str, path: str, content: str | bytes = '', bundle: str | dspyce.bitstreams.Bundle.Bundle = 'ORIGINAL', uuid: str = None, primary: bool = False, show: bool = True)
 |  
 |  A class for managing content files in the saf-packages.
 |  
 |  Methods defined here:
 |  
 |  __init__(self, content_type: str, name: str, path: str, content: str | bytes = '', bundle: str | dspyce.bitstreams.Bundle.Bundle = 'ORIGINAL', uuid: str = None, primary: bool = False, show: bool = True)
 |      Creates a new Bitstream object.
 |      
 |      :param content_type: The type of content file. Must be one off: ('relations', 'licenses', 'images', 'contents',
 |      'handle', 'other')
 |      :param name: The name of the bitstream.
 |      :param path: The path, where the file is currently stored.
 |      :param content: The content of the file, if it shouldn't be loaded from the system.
 |      :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
 |      :param uuid: The uuid of the bitstream if existing.
 |      :param primary: Primary is used to specify the primary bitstream.
 |      :param show: If the bitstream should be listed in the saf-content file. Default: True - if the type is relations
 |      or handle the default is False.
 |  
 |  __str__(self)
 |      Provides all information about the DSpace-Content file.
 |      
 |      :return: A SAF-ready information string which can be used for the content-file.
 |  
 |  add_description(self, description)
 |      Creates a description to the content-file.
 |      
 |      :param description: String which provides the description.
 |  
 |  add_permission(self, rw: str, group_name: str)
 |      Add access information to the Bitstream.
 |      
 |      :param rw: Access-type r-read, w-write.
 |      :param group_name: Group to which the access will be provided.
 |  
 |  get_bitstream_file(self)
 |      Returns the actual file as a TextIOWrapper object.
```
### IIIFBitstream
```
class IIIFBitstream(dspyce.bitstreams.Bitstream.Bitstream)
 |  IIIFBitstream(content_type: str, name: str, path: str, content: str | bytes = '', bundle: str | dspyce.bitstreams.Bundle.Bundle = 'ORIGINAL', primary: bool = False, show: bool = True)
 |  
 |  A class for managing iiif-specific content files in the saf-packages.
 |  
 |  Method resolution order:
 |      IIIFBitstream
 |      dspyce.bitstreams.Bitstream.Bitstream
 |      builtins.object
 |  
 |  Methods defined here:
 |  
 |  __init__(self, content_type: str, name: str, path: str, content: str | bytes = '', bundle: str | dspyce.bitstreams.Bundle.Bundle = 'ORIGINAL', primary: bool = False, show: bool = True)
 |      Creates a new IIIF-Bitstream object.
 |      
 |      :param content_type: The type of content file. Must be one of: 'images'
 |      :param name: The name of the bitstream.
 |      :param path: The path, where the file is currently stored.
 |      :param content: The content of the file, if it shouldn't be loaded from the system.
 |      :param bundle: The bundle, where the bitstream should be placed in. The default is ORIGINAL.
 |      :param primary: Primary is used to specify the primary bitstream.
 |      :param show: If the bitstream should be listed in the saf-content file. Default: True - if the type is relations
 |      or handle the default is False.
 |  
 |  __str__(self)
 |      Provides all information about the DSpace IIIF-Content file.
 |      
 |      :return: A SAF-ready information string which can be used for the content-file.
 |  
 |  add_iiif(self, label: str, toc: str, w: int = 0)
 |      Add  IIIF-information for the bitstream.
 |      
 |      :param label: is the label that will be used for the image in the viewer.
 |      :param toc: is the label that will be used for a table of contents entry in the viewer.
 |      :param w: is the image width to reduce it. Default 0
 |  
 |  ----------------------------------------------------------------------
 |  Data and other attributes defined here:
 |  
 |  __annotations__ = {'iiif': dict[str, str | int]}
 |  
 |  ----------------------------------------------------------------------
 |  Methods inherited from dspyce.bitstreams.Bitstream.Bitstream:
 |  
 |  add_description(self, description)
 |      Creates a description to the content-file.
 |      
 |      :param description: String which provides the description.
 |  
 |  add_permission(self, rw: str, group_name: str)
 |      Add access information to the Bitstream.
 |      
 |      :param rw: Access-type r-read, w-write.
 |      :param group_name: Group to which the access will be provided.
 |  
 |  get_bitstream_file(self)
 |      Returns the actual file as a TextIOWrapper object.
```