import os
import re
from typing import List
from .ContentFile import ContentFile
from .Relation import Relation
from .Relation import export_relations


class DSpace:
    """
        Diese Klasse dient dem Import von Items und deren Meta_Daten in DSpace-Systeme.
    """
    path: str
    metadata: dict  # {prefix: [{element: '', qualifier: '', value:''}, ...], ...}
    element_id: int
    relations: list
    contents: List[ContentFile]
    handle: str

    def __init__(self, element_id: int, path: str = '', schema: list = None, entity: str = '', handle: str = ''):
        """
            Erstellt ein neues Objekt der Klasse.

            :param element_id: Die ID des elements. Wird zur Benennung des Ordners benötigt.
            :param path: Der Pfad unterdem die Import-Daten gespeichert werden.
            :param schema: Eine Liste mit weiteren Metadaten Schemata abgesehen von dublin_core.
            :param handle: Der Handle des objects, wenn vorhanden.
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

    def add_dc_value(self, element: str, value, qualifier: str = 'none'):
        """
            Fügt ein neues dc Metadatenfeld inklusive Inhalt hinzu.

            :param element: Der Typ des Metadatenfeldes. Zum Beispiel 'title'
            :param value: Der Wert des Metadatenfeldes.
            :param qualifier: Der Qualifier des Feldes. Default: None
        """
        if type(value) is list:
            for i in value:
                self.add_metadata(element, i, 'dc', qualifier)
        else:
            self.add_metadata(element, value, 'dc', qualifier)

    def add_metadata(self, element: str, value: str, prefix: str, qualifier: str = 'none'):
        """
            Fügt ein neues allgemeines Metadatenfeld inklusive Inhalt hinzu. Das
            Schema wird durch den prefix spezifiziert.

            :param element: Der Typ des Metadatenfeldes. Zum Beispiel 'title'
            :param value: Der Wert des Metadatenfeldes.
            :param prefix: Der prefix des Metadatenschemas.
            :param qualifier: Der Qualifier des Feldes. Default: None
        """
        try:
            if type(value) is list:
                for i in value:
                    self.metadata[prefix].append({'element': element, 'qualifier': qualifier, 'value': i})
            elif value == '':
                return
            else:
                self.metadata[prefix].append({'element': element, 'qualifier': qualifier, 'value': value})
        except KeyError:
            raise KeyError('The prefix %s doesn\'t exist.' % prefix)

    def add_relation(self, relation_type: str, handle: str):
        """
            Fügt eine neue Beziehung zu dem Datensatz hinzu.

            :param relation_type: Die Bezeichnung der Beziehung.
            :param handle: Die eindeutige Bezeichnung für das Objekt der Beziehung.
        """
        self.relations.append(Relation(relation_type, handle))

    def add_content(self, content_file: str, path: str, description: str = '', w: int = 0, server: str = ''):
        """
            Fügt zusätzliche Content-Files zum Dokument hinzu.

            :param content_file: Der Name des hinzuzufügenden Dokumentes.
            :param path: Der Pfad unter dem das Dokument zu finden ist.
            :param description: Eine Beschreibung zu dem Content-File.
            :param w: Die Breite eines Bildes. Nur relevant, wenn es sich um ein jpg handelt und dies verkleinert werden
            soll.
            :param server: Enthält den Namen des Servers, auf welchem das Bild liegt. Ist leer, falls das Bild lokal
            vorliegt
        """
        cf = None
        if re.search(r'\.jpg', content_file) or re.search(r'\.tif[f]?', content_file):
            cf = ContentFile('images', content_file, path, server=server)
            name = content_file.split('.')[0]
            cf.add_iiif('Digitalisat-%s' % name, name, w=w)
            cf.add_description(description)
            self.contents.append(cf)
        else:
            cf = ContentFile('other', content_file, path)
        if description != '':
            cf.add_description(description)

    def dc_schema(self) -> str:
        """
            Erstellt den Inhalt der Datei dublin_core.xml.

            :return: Ein String im xml-Format.
        """
        dc_xml = '<dublin_core>\n'
        for m in self.metadata['dc']:
            dc_xml += '\t<dcvalue element="{}" qualifier="{}">{}</dcvalue>\n'.format(m['element'], m['qualifier'],
                                                                                     m['value'])
        dc_xml += '</dublin_core>'
        return dc_xml

    def prefix_schema(self, prefix: str) -> str:
        """
            Erstellt den Inhalt der Dateien metadata_[prefix].xml

            :param prefix: Der Präfix des Schemas, das erstellt werden soll.
        """
        if prefix not in self.metadata.keys():
            raise KeyError('Prefix "%s" does\'nt exist!')
        prefix_xml = '<dublin_core schema="{}">\n'.format(prefix)
        for m in self.metadata[prefix]:
            prefix_xml += '\t<dcvalue element="{}" qualifier="{}">{}</dcvalue>\n'.format(m['element'], m['qualifier'],
                                                                                         m['value'])
        prefix_xml += '</dublin_core>'
        return prefix_xml

    def create_dir(self, overwrite: bool = False):
        """
            Erstellt das item im archive_directory. Benötigt daher den Ordner
            "archive_directory", existiert dieser noch nicht, wird er neu
            erstellt.
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
