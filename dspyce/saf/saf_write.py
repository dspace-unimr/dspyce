# saf/saf_write.py
"""
Python module for creating saf packages to prepare DSpace Item-imports or updates. Two functions are imported by the saf
package:
1. create_saf_package() -> Creates a single saf package based on a given Item.
2. saf_packages() -> Creates multiple saf packages in a given path based on the given Item information.
"""
import logging
import os
from bs4 import BeautifulSoup
from bs4.formatter import XMLFormatter

from dspyce.Item import Item
from dspyce.Relation import Relation
from dspyce.metadata import MetaData


LOG_LEVEL = logging.INFO
"""A global log_level for logging. Is used by all sub-modules as a default value for the log-level."""

LOG_FILE: str | None = None
"""
A global log-file for logging. Is used by all sub-modules as default. If "NONE" all logs will be printed into the
console.
"""

LOG_FORMAT: str = '%(asctime)s - %(levelname)s: %(message)s'
"""A global log-format setting, wich is used by all sub-modules."""


def export_relations(relations: list[Relation]) -> str:
    """
        Creates a list of relationships separated by line-breaks. It can be used to create the relationship-file in a
        saf-package.

        :param relations: A list of objects of the class "Relation"
        :return: The line-break separated list of relationships as a string.
    """
    relation_strings = list(map(lambda x: ':'.join(str(x).split(':')[1:]), relations))
    return '\n'.join([r.replace(':', ' ') for r in relation_strings])


def save_text_file(path: str, file_name: str, content: str):
    """
    Save a text into path using encoding *utf-8*. Raises an exception if the file already exists.

    :param path: The path where to store the text-file.
    :param file_name: The name of the new file.
    :param content: The content of the text-file.
    :raises FileExistsError: If the file already exits in path.
    """
    if file_name in os.listdir(path):
        raise FileExistsError(f'The file {file_name} already exists in path {path}.')
    with open(f'{path}/{file_name}', 'w', encoding='utf8') as f:
        f.write(content)
        logging.debug(f'Wrote file "{file_name}" into "{path}"')


def create_bitstreams(item: Item, save_path: str):
    """
       Creates the need bitstream-files in the archive-directory based on the path information.

        :param item: The item to create the bitstreams for.
        :param save_path: The path, where the bitstream shall be saved.
   """
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE, encoding='utf8',
                        format=LOG_FORMAT)
    contents = []
    bundles = item.get_bundles()
    for bundle in bundles:
        for b in bundle.bitstreams:
            if b.bundle.name != bundle.name:
                logging.error(f'The name of the bundle({bundle.name}) containing the bitstream({b.file_name}) does not'
                              f'match the name of the bundle registered in the bitstream object: {b.bundle.name}')
            contents.append(str(b))

            b.save_bitstream(save_path)
            logging.debug(f'Successfully created file {b.file_name}')
    if len(contents) > 0:
        save_text_file(save_path, 'contents', '\n'.join(contents))


def export_schemas(metadata: MetaData) -> dict:
    """
    Creates the content of the xml files metadata_[prefix].xml based on the given metadata.

    :param metadata: The metadata object containing all metadata fields.
    :return: The content of the xml file for this schema prefix in a dictionary.
    """
    class SAFFormatter(XMLFormatter):
        def attributes(self, tag):
            for k, l in tag.attrs.items():
                yield k, l

    xml_schemas = {}
    for prefix in metadata.get_schemas():
        schema_xml = BeautifulSoup(features='xml', preserve_whitespace_tags=["dcvalue"])
        file_name = f'metadata_{prefix}.xml'
        if prefix == 'dc':
            file_name = 'dublin_core.xml'
            schema_xml.append(schema_xml.new_tag('dublin_core'))
        else:
            schema_xml.append(schema_xml.new_tag('dublin_core', schema=prefix))
        metadata_dict = metadata.get_by_schema(prefix)
        for m in metadata_dict.keys():
            tag = m.split('.')
            element, qualifier = tag[1], tag[2] if len(tag) > 2 else None
            for v in metadata_dict[m]:
                mv_field = schema_xml.new_tag("dcvalue", element=element)
                if qualifier is not None:
                    mv_field["qualifier"] = qualifier
                if v.language is not None and v.language != '':
                    mv_field["language"] = v.language
                mv_field.string = v.value
                schema_xml.contents[0].append(mv_field)
        xml_schemas[file_name] = schema_xml.prettify(formatter=SAFFormatter())
    return xml_schemas


def create_saf_package(item: Item, element_id: int, path: str, overwrite: bool = False):
    """
    Creates a saf package folder for an item object.

    :param item: The Item to create the package of.
    :param element_id: An id added to the directory name, aka item_<element_id>
    :param path: The path where to store all package files.
    :param overwrite: If true, it overwrites the currently existing files.
    """

    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE, encoding='utf8',
                        format=LOG_FORMAT)

    path += '/' if len(path) > 0 and path[-1] != '/' else ('./' if len(path) == 0 else '')
    if 'archive_directory' not in os.listdir(path):
        os.mkdir(path + 'archive_directory')
        logging.info(f'Created directory *archive_directory* in "{path}"')
    path += 'archive_directory/'
    # Now we check, if the element already exists and deleted it, if overwrite is set to true.
    if f'item_{element_id}' in os.listdir(path):
        logging.debug(f'The Item "{element_id}" already exists in "{path}".')
        if not overwrite:
            logging.error(f'The item with the id {element_id} already exists in "{path}"!')
            raise FileExistsError(f'The item with the element_id "{element_id}" exists already'
                                  f'in "{path}"')
        else:
            logging.debug(f'Deleted old item "{element_id}" in "{path}"')
            for file in os.listdir(f'{path}/item_{element_id}'):
                os.remove(f'{path}/item_{element_id}/{file}')
            os.rmdir(f'{path}/item_{element_id}')

    os.mkdir(f'{path}item_{element_id}')
    logging.info(f'Created directory for item with the ID {element_id}')
    path += f'item_{element_id}/'

    xml_files = export_schemas(item.metadata)
    for file_name in xml_files.keys():
        save_text_file(path, file_name, str(xml_files[file_name]))
        logging.debug('Wrote %s to item folder item_%s' % (file_name, element_id))

    if len(item.relations) > 0:
        save_text_file(path, 'relationships', export_relations(item.relations))
        logging.debug(f'Created relations file for item {element_id}')
    if item.handle != '':
        save_text_file(path, 'handle', item.handle)
        logging.debug(f'Created handle file for item {element_id}')
    if len(item.collections) > 0:
        save_text_file(path, 'collections', '\n'.join([c.get_identifier() for c in item.collections]))
        logging.debug(f'Created collections file for item {element_id}')
    create_bitstreams(item, save_path=path)


def saf_packages(items: list[Item], path: str, overwrite: bool = False):
    """
    Creates a list of saf packages based on a given item list and writes them down in the filesystem.

    :param items: The list of items to create the packages from.
    :param path: The path in the filesystem where to store the packages.
    :param overwrite: If true, it overwrites the currently existing files.
    """
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE, encoding='utf8',
                        format=LOG_FORMAT)
    n = 0
    show_progress = len(items) >= 1000
    logging.info(f'Start process! Processing {len(items)}')
    for item in items:
        create_saf_package(item, n, path, overwrite)
        if show_progress and n % 100 == 0:
            logging.info(f'\tCreated {n} saf packages.')
        n += 1
    logging.info(f'Finished process! Created {len(items)} saf packages.')
