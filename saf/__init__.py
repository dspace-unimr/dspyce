# saf/__init__.py
"""
Module for creating saf packages for DSpace item-imports and -updates.

"""

from Item import Item
from Relation import Relation
from ContentFile import ContentFile
from MetaData import MetaDataList
import os


def export_relations(relations: list[Relation]) -> str:
    """
        Creates a list of relationships separated by line-breaks. It can be used to create the relationship-file in a
        saf-package.

        :param relations: A list of objects of the class "Relation"
        :return: The line-break separated list of relationships as a string.
    """
    return '\n'.join([str(r).replace(':', ' ') for r in relations])


def create_bitstreams(bitstreams: list[ContentFile], save_path: str):
    """
       Creates the need bitstream-files in the archive-directory based on the path information.

       :param bitstreams: A list of bitstreams to create the files from.
       :param save_path: The path, where the bitstream shall be saved.
   """
    contents = ''
    for b in bitstreams:
        if b.show:
            contents += f'{str(b)}\n'
        if b.file is None:
            with open(b.path + b.file_name, 'rb') as f:
                b.file = f.read()

        with open(save_path + b.file_name, 'wb' if type(b.file) is bytes else 'w') as f:
            file: bytes | str = b.file
            f.write(file)
    if contents != '':
        with open(save_path + 'contents', 'w', encoding='utf8') as f:
            f.write(contents)


def create_saf_package(item: Item, element_id: int, path: str, overwrite: bool = False):
    """
    Creates a saf package folder for an item object.

    :param item: The Item to create the package of.
    :param element_id: An id added to the directory name, aka item_<element_id>
    :param path: The path where to store all package files.
    :param overwrite: If true, it overwrites the currently existing files.
    """
    def prefix_schema(prefix: str, metadata: MetaDataList) -> str:
        """
        Creates the content of the files metadata_[prefix].xml

        :param prefix: The prefix of the schema which should be created.
        :param metadata: The metadata list containing all metadatafields.
        """
        if prefix not in metadata.get_schemas():
            raise KeyError(f'The Prefix "{prefix}" does\'nt exist!')
        schema = '' if prefix == 'dc' else f' schema="{prefix}"'
        prefix_xml = f'<dublin_core{schema}>\n'
        for m in filter(lambda x: x.schema == prefix, metadata):
            lang = f' language="{m.language}"' if m.language is not None else ''
            prefix_xml += (f'\t<dcvalue element="{m.element}" qualifier="{m.qualifier}"{lang}>'
                           f'{m.value}'
                           '</dcvalue>\n')
        prefix_xml += '</dublin_core>'
        return prefix_xml

    if 'archive_directory' not in os.listdir(path):
        os.mkdir(path + 'archive_directory')
    path += 'archive_directory/'
    exists_error = FileExistsError(f'The item with the element_id "{element_id}" exists already'
                                   f'in "{path}"')
    if f'item_{element_id}' in os.listdir(path) and not overwrite:
        raise exists_error
    else:
        try:
            os.mkdir(f'{path}item_{element_id}')
        except FileExistsError:
            if not overwrite:
                raise exists_error
    path += f'item_{element_id}/'
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    if 'dc' in item.metadata.get_schemas():
        with open(path + 'dublin_core.xml', 'w', encoding='utf8') as f:
            f.write(header + prefix_schema('dc', item.metadata))
    for k in filter(lambda x: x != 'dc', item.metadata.get_schemas()):
        with open(f'{path}metadata_{k}.xml', 'w', encoding='utf8') as f:
            f.write(header + prefix_schema(k, item.metadata))

    if len(item.relations) > 0:
        item.contents.append(ContentFile('relations', 'relationships', '',
                                         export_relations(item.relations), show=False))
    if item.handle != '':
        item.contents.append(ContentFile('handle', 'handle', '', item.handle, show=False))
    if len(item.collections) > 0:
        item.contents.append(ContentFile('collections', 'collections', '',
                                         '\n'.join([c.handle for c in item.collections]), show=False))
    create_bitstreams(item.contents, save_path=path)
