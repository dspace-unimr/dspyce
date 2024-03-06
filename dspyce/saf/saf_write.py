# saf/saf_write.py
"""
Python module for creating saf packages to prepare DSpace Item-imports or updates. Two functions are imported by the saf
package:
1. create_saf_package() -> Creates a single saf package based on a given Item.
2. saf_packages() -> Creates multiple saf packages in a given path based on the given Item information.
"""
import logging
import os

from ..Item import Item
from ..Relation import Relation
from ..bitstreams.ContentFile import ContentFile
from ..metadata import MetaDataList


def export_relations(relations: list[Relation]) -> str:
    """
        Creates a list of relationships separated by line-breaks. It can be used to create the relationship-file in a
        saf-package.

        :param relations: A list of objects of the class "Relation"
        :return: The line-break separated list of relationships as a string.
    """
    relation_strings = list(map(lambda x: ':'.join(str(x).split(':')[1:]), relations))
    return '\n'.join([r.replace(':', ' ') for r in relation_strings])


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

        with open(save_path + b.file_name, 'wb' if isinstance(b.file, bytes) else 'w') as f:
            logging.debug(f'Sucessfully created file {b.file_name}')
            file: bytes | str = b.file
            f.write(file)
    if contents != '':
        with open(save_path + 'contents', 'w', encoding='utf8') as f:
            f.write(contents)
        logging.debug(f'Wrote content-file {save_path + contents}')


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
        :param metadata: The metadata list containing all metadata fields.
        """
        if prefix not in metadata.get_schemas():
            raise KeyError(f'The Prefix "{prefix}" does\'nt exist!')
        schema = '' if prefix == 'dc' else f' schema="{prefix}"'
        prefix_xml = f'<dublin_core{schema}>\n'
        for m in filter(lambda x: x.schema == prefix, metadata):
            value = [m.value] if not isinstance(m.value, list) else m.value
            for v in value:
                lang = f' language="{m.language}"' if m.language is not None else ''
                prefix_xml += (f'\t<dcvalue element="{m.element}" qualifier="{m.qualifier}"{lang}>'
                               f'{v}'
                               '</dcvalue>\n')
        prefix_xml += '</dublin_core>'
        return prefix_xml

    path += '/' if len(path) > 0 and path[-1] != '/' else ('./' if len(path) == 0 else '')
    if 'archive_directory' not in os.listdir(path):
        os.mkdir(path + 'archive_directory')
        logging.info(f'Created archive_directory in "{path}"')
    path += 'archive_directory/'
    exists_error = FileExistsError(f'The item with the element_id "{element_id}" exists already'
                                   f'in "{path}"')
    if f'item_{element_id}' in os.listdir(path) and not overwrite:
        logging.error(f'The item with the id {element_id} already exists in "{path}"!')
        raise exists_error

    os.mkdir(f'{path}item_{element_id}')
    logging.info(f'Created directory for item with the ID {element_id}')
    path += f'item_{element_id}/'
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    if 'dc' in item.metadata.get_schemas():
        with open(path + 'dublin_core.xml', 'w', encoding='utf8') as f:
            f.write(header + prefix_schema('dc', item.metadata))
        logging.debug(f'Wrote dublin_core.xml to item folder item_{element_id}')
    for k in filter(lambda x: x != 'dc', item.metadata.get_schemas()):
        with open(f'{path}metadata_{k}.xml', 'w', encoding='utf8') as f:
            f.write(header + prefix_schema(k, item.metadata))

        logging.debug(f'Wrote metadata_{k}.xml to item folder item_{element_id}')

    if len(item.relations) > 0:
        item.contents.append(ContentFile('relations', 'relationships', '',
                                         export_relations(item.relations), show=False))
    if item.handle != '':
        item.contents.append(ContentFile('handle', 'handle', '', item.handle, show=False))
    if len(item.collections) > 0:
        item.contents.append(ContentFile('collections', 'collections', '',
                                         content='\n'.join([c.get_identifier() for c in item.collections]), show=False))
        logging.debug(f'Created handle file for item {element_id}')
    create_bitstreams(item.contents, save_path=path)


def saf_packages(items: list[Item], path: str, overwrite: bool = False):
    """
    Creates a list of saf packages based on a given item list and writes them down in the filesystem.

    :param items: The list of items to create the packages from.
    :param path: The path in the filesystem where to store the packages.
    :param overwrite: If true, it overwrites the currently existing files.
    """
    n = 0
    show_progress = len(items) >= 1000
    logging.info(f'Start process! Processing {len(items)}')
    for item in items:
        create_saf_package(item, n, path, overwrite)
        if show_progress and n % 100 == 0:
            logging.info(f'\tCreated {n} saf packages.')
        n += 1
    logging.info(f'Finished process! Created {len(items)} saf packages.')
