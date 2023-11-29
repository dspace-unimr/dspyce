import os
import re
from .ContentFile import ContentFile
from .Relation import Relation
from .Relation import export_relations


class DSpace:
    """
    This class helps to import and update items and there metadata via simple-archive-format in DSpace-Systems.
    """
    path: str
    metadata: dict  # {prefix: [{element: '', qualifier: '', value:''}, ...], ...}
    element_id: int
    relations: list
    contents: list[ContentFile]
    handle: str

    def __init__(self, element_id: int, path: str = '', schema: list = None, entity: str = '', handle: str = ''):
        """
        Creates a new Object of the class DSpace.

        :param element_id: The ID of an element. It is needed to name the folders.
        :param path: The path, where the saf-packages should be saved.
        :param schema: A list of further metadata-schemas additionally to dublin-core.
        :param handle: The handle of the object, if existing.
        """
        self.path = path
        self.metadata = {}
        self.element_id = element_id
        schema = schema if schema is not None else []
        self.metadata['dc'] = []
        for s in schema:
            self.metadata[s] = []
        if entity != '':
            self.metadata['dspace'] = []
            self.add_metadata(element="entity", qualifier='type', value=entity, prefix='dspace')
        self.relations = []
        self.contents = []
        self.handle = handle

    def add_dc_value(self, element: str, value: str, qualifier: str = 'none', language: str = None):
        """
        Creates a new dc- metadata field with the given value.

        :param element: Type of the metadata-field. For example 'title'.
        :param value: The value of the metadata-field.
        :param qualifier: The qualifier of the field. Default: None
        :param language: The language of the metadata field. Default: None.
        """
        if type(value) is list:
            for i in value:
                self.add_metadata(element, i, 'dc', qualifier, language)
        else:
            self.add_metadata(element, value, 'dc', qualifier, language)

    def add_metadata(self, element: str, value: str, prefix: str, qualifier: str = 'none', language: str = None):
        """
        Creates a new metadata field with the given value. The schema is specified through the prefix parameter.

        :param element: Type of the metadata-field. For example 'title'.
        :param value: The value of the metadata-field.
        :param prefix: The prefix of the schema, which should be used.
        :param qualifier: The qualifier of the field. Default: None
        :param language: The language of the metadata field.
        """
        try:
            if type(value) is list:
                for i in value:
                    self.metadata[prefix].append({'element': element, 'qualifier': qualifier, 'value': i,
                                                  'language': language})
            elif value == '':
                return
            else:
                self.metadata[prefix].append({'element': element, 'qualifier': qualifier, 'value': value,
                                              'language': language})
        except KeyError:
            raise KeyError(f"The prefix '{prefix}' doesn't exist.")

    def add_relation(self, relation_type: str, handle: str):
        """
        Creates a new relationship to the item.

        :param relation_type: The name of the relationship.
        :param handle: The identifier of the related object.
        """
        self.relations.append(Relation(relation_type, handle))

    def add_content(self, content_file: str, path: str, description: str = '', width: int = 0):
        """
        Adds additional content-files to the item.

        :param content_file: The name of the document, which should be added.
        :param path: The path where to find the document.
        :param description: A description of the content file.
        :param width: The width of an image. Only needed, if the file is a jpg, wich should be reduced.
        :param server: Contains the name of the server on which the image is stored, if so. Stays empty in case of a
         local image.
        """

        if re.search(r'\.jpg', content_file) or re.search(r'\.tiff?', content_file):
            cf = ContentFile('images', content_file, path)
            name = content_file.split('.')[0]
            cf.add_iiif('Digitalisat-%s' % name, name, w=width)
            cf.add_description(description)
            self.contents.append(cf)
        else:
            cf = ContentFile('other', content_file, path)
        if description != '':
            cf.add_description(description)

    def dc_schema(self) -> str:
        """
        Creates the content of the file dublin_core.xml

        :return: Ein String im xml-Format.
        """
        return self.prefix_schema('dc')

    def prefix_schema(self, prefix: str) -> str:
        """
            Creates the content of the files metadata_[prefix].xml

            :param prefix: The prefix of the schema which should be created.
        """
        if prefix not in self.metadata.keys():
            raise KeyError(f'The Prefix "{prefix}" does\'nt exist!')
        schema = '' if prefix == 'dc' else f' schema="{prefix}"'
        prefix_xml = f'<dublin_core{schema}>\n'
        for m in self.metadata[prefix]:
            lang = f' language="{m["language"]}"' if m["language"] is not None else ''
            prefix_xml += (f'\t<dcvalue element="{m["element"]}" qualifier="{m["qualifier"]}"{lang}>'
                           f'{m["value"]}'
                           '</dcvalue>\n')
        prefix_xml += '</dublin_core>'
        return prefix_xml

    def create_dir(self, overwrite: bool = False):
        """
        Creates the item in folder named 'archive_directory'. If the folder doesn't exist yet. It will be created.

        :param overwrite: If true, it overwrites the currently existing files.
        """
        local_path = self.path
        if 'archive_directory' not in os.listdir(local_path):
            os.mkdir(local_path + 'archive_directory')
        local_path += 'archive_directory/'
        exists_error = FileExistsError(f'The item with the element_id "{self.element_id}" exists already'
                                       f'in "{self.path}"')
        if f'item_{self.element_id}' in os.listdir(local_path) and not overwrite:
            raise exists_error
        else:
            try:
                os.mkdir(f'{local_path}item_{self.element_id}')
            except FileExistsError:
                if not overwrite:
                    raise exists_error
        local_path += 'item_%s/' % self.element_id
        header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        with open(local_path + 'dublin_core.xml', 'w', encoding='utf8') as f:
            f.write(header + self.dc_schema())
        for k in filter(lambda x: x != 'dc', self.metadata.keys()):
            with open(local_path + 'metadata_{}.xml'.format(k), 'w', encoding='utf8') as f:
                f.write(header + self.prefix_schema(k))
        if len(self.relations) > 0:
            self.contents.append(ContentFile('relations', 'relationships', '',
                                             export_relations(self.relations)))
            # with open(local_path + 'relationships', 'w', encoding='utf8') as f:
            #    f.write(export_relations(self.relations))
        if self.handle != '':
            self.contents.append(ContentFile('handle', 'handle', '', self.handle))
        content_file = ''
        for c in self.contents:
            if c.show:
                content_file += str(c) + '\n'
            c.create_file(local_path)
        if content_file != '':
            cf = ContentFile('contents', 'contents', '', content_file)
            cf.create_file(local_path)

    def __str__(self):
        header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        dc_file = header + self.dc_schema()

        other_prefix = ''
        for k in filter(lambda x: x != 'dc', self.metadata.keys()):
            other_prefix += '*%s*\n' % k
            other_prefix += header + self.prefix_schema(k) + '\n\n'

        relation_file = ''
        if len(self.relations) > 0:
            relation_file = export_relations(self.relations)
        content_file = ''
        if len(self.contents) > 0:
            contents_text = ''
            for i in self.contents:
                contents_text += str(i) + '\n'
            content_file = contents_text
        return dc_file + '\n\n' + other_prefix + relation_file + '\n\n' + content_file

    def __len__(self) -> int:
        """
        Counts the number of metadata fields for the given item.

        :return: The number as an integer value.
        """
        return sum(len(m) for m in self.metadata.values())
