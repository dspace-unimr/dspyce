# saf/saf_read.py
"""
Python module for reading out saf_packages to create dspyce.Item objects

1. read_saf_package() -> Reads a single saf package and creates the Item object.
2. read_saf_packages() -> Reads all found saf packages in the provided path and returns the Item objects based on
the read_saf_packages() function.
"""

import os
import re
import uuid
from bs4 import BeautifulSoup

from dspyce.Item import Item
from dspyce.Collection import Collection
from dspyce.bitstreams import Bundle


def read_saf_package(path: str) -> Item:
    """
    Reads a single saf package and creates the Item based on the found metadata, bitstreams, collections, handles and
    relationships.

    :param path: The path where to find the directory of the saf-package.
    :return: The Item object for the saf-package.
    """
    path = path[:-1] if path.endswith('/') else path
    files = os.listdir(path)
    metadata_files = filter(lambda x: re.search(r'((metadata_[a-zA-Z\-]+)|(dublin_core))\.xml$', x), files)
    further_information: dict[str: list] = {'contents': [], 'collections': [], 'relationships': []}
    handle = ''
    for file_name in ('contents', 'collections', 'relationships'):
        if file_name in files:
            with open(f'{path}/{file_name}', encoding='utf-8') as f:
                further_information[file_name] = f.read().splitlines()
    if 'handle' in files:
        with open(f'{path}/handle', encoding='utf-8') as f:
            handle = f.read().splitlines()[0].strip()
    item = Item(handle=handle)
    for md_file in metadata_files:
        with open(f'{path}/{md_file}', encoding='utf-8') as f:
            xml_content = f.read()
        bs = BeautifulSoup(xml_content, 'xml').find('dublin_core')
        schema = bs.get('schema')
        if schema is None:
            schema = 'dc'
        for field in bs.find_all('dcvalue'):
            element = field.get('element')
            qualifier = field.get('qualifier')
            qualifier = None if qualifier is None or qualifier == 'none' or qualifier.strip() == '' else qualifier
            tag = f'{schema}.{element}' + (f'.{qualifier}' if qualifier is not None else '')
            lang = field.get('language')
            item.add_metadata(tag, field.get_text(), lang)

    for c in further_information['collections']:
        try:
            item.add_collection(Collection(uuid=str(uuid.UUID(c))))
        except ValueError:
            item.add_collection(Collection(handle=c))

    for r in filter(lambda x: x.strip() != '', further_information['relationships']):
        relation = r.split(' ')
        item.add_relation(relation[0].replace('relation.', ''), relation[1])
    for b in filter(lambda x: x.strip() != '', further_information['contents']):
        bitstream = b.split('\t')
        name = bitstream[0]
        try:
            attributes = {i.split(':')[0]: i.split(':')[1] for i in bitstream[1:]}
        except IndexError:
            raise AttributeError(f'Found incorrect formated attributes could not parse attribute in {bitstream[1:]}')
        description = attributes.get('description') if attributes.get('description') is not None else ''
        bundle = attributes.get('bundle') if attributes.get('bundle') is not None else Bundle.DEFAULT_BUNDLE
        permissions = [(p.split(' ')[0], p.split(' ')[1])
                       for p in attributes.get('permissions')] if attributes.get('permissions') is not None else None

        iiif = 'iiif-label' in attributes.keys()
        item.add_content(name, f'{path}', description, bundle=bundle, permissions=permissions, iiif=iiif,
                         iiif_toc=attributes['iiif-toc'] if 'iiif-toc' in attributes.keys() else '')
    return item


def read_saf_packages(path: str) -> list[Item]:
    """
    Read all SAF-packages stored in the directory provided by path.

    :param path: The directory where the saf_packages are stored in.
    :return: A list of Item objects built based on the information provided by the SAF-packages.
    """
    return [read_saf_package(f'{path}/{directory}') for directory in os.listdir(path)]
