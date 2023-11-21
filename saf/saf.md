# Table of Contents

* [saf](#saf)
* [saf.Relation](#saf.Relation)
  * [Relation](#saf.Relation.Relation)
    * [\_\_init\_\_](#saf.Relation.Relation.__init__)
  * [export\_relations](#saf.Relation.export_relations)
* [saf.DSpace](#saf.DSpace)
  * [DSpace](#saf.DSpace.DSpace)
    * [metadata](#saf.DSpace.DSpace.metadata)
    * [\_\_init\_\_](#saf.DSpace.DSpace.__init__)
    * [add\_dc\_value](#saf.DSpace.DSpace.add_dc_value)
    * [add\_metadata](#saf.DSpace.DSpace.add_metadata)
    * [add\_relation](#saf.DSpace.DSpace.add_relation)
    * [add\_content](#saf.DSpace.DSpace.add_content)
    * [dc\_schema](#saf.DSpace.DSpace.dc_schema)
    * [prefix\_schema](#saf.DSpace.DSpace.prefix_schema)
    * [create\_dir](#saf.DSpace.DSpace.create_dir)
    * [\_\_len\_\_](#saf.DSpace.DSpace.__len__)
* [saf.ContentFile](#saf.ContentFile)
  * [ContentFile](#saf.ContentFile.ContentFile)
    * [\_\_init\_\_](#saf.ContentFile.ContentFile.__init__)
    * [add\_description](#saf.ContentFile.ContentFile.add_description)
    * [add\_permission](#saf.ContentFile.ContentFile.add_permission)
    * [add\_iiif](#saf.ContentFile.ContentFile.add_iiif)
    * [create\_file](#saf.ContentFile.ContentFile.create_file)

<a id="saf"></a>

# saf

Module for creating saf packages for DSpace item-imports and -updates.

<a id="saf.Relation"></a>

# saf.Relation

This module contains the python class Relation representing the Relation between DSpace-Entities.
And the following function:
- `export_relations(relations: list)` - Returns a list of relationships in a string.

**Example**:

  
  >from saf.Relation import export_relations
  >
  >export_relations([Relation('any_relation', '123456789/12'), Relation('different_relation', '123456789/13')])
  
  > relation.any_relation 123456789/12
  relation.different_relation 123456789/13

<a id="saf.Relation.Relation"></a>

## Relation Objects

```python
class Relation()
```

The class Relation represents the relation between different DSPACE-entities. It stores the relation-type
(relation_key) and id of the related Item.

<a id="saf.Relation.Relation.__init__"></a>

#### \_\_init\_\_

```python
def __init__(relation_key: str, related_item: str)
```

Creates a new object of the class relation, which represents exactly

one DSpace-Relation

**Arguments**:

- `relation_key`: The relation-type, aka the name.
- `related_item`: The handle/uuid/item-saf-id of the entity, to which the item is related.

<a id="saf.Relation.export_relations"></a>

#### export\_relations

```python
def export_relations(relations: list[Relation]) -> str
```

Creates a list of relationships separated by line-breaks. It can be used to create the relationship-file in a

saf-package.

**Arguments**:

- `relations`: A list of objects of the class "Relation"

**Returns**:

The line-break separated list of relationships as a string.

<a id="saf.DSpace"></a>

# saf.DSpace

<a id="saf.DSpace.DSpace"></a>

## DSpace Objects

```python
class DSpace()
```

This class helps to import and update items and there metadata via simple-archive-format in DSpace-Systems.

<a id="saf.DSpace.DSpace.metadata"></a>

#### metadata

{prefix: [{element: '', qualifier: '', value:''}, ...], ...}

<a id="saf.DSpace.DSpace.__init__"></a>

#### \_\_init\_\_

```python
def __init__(element_id: int,
             path: str = '',
             schema: list = None,
             entity: str = '',
             handle: str = '')
```

Creates a new Object of the class DSpace.

**Arguments**:

- `element_id`: The ID of an element. It is needed to name the folders.
- `path`: The path, where the saf-packages should be saved.
- `schema`: A list of further metadata-schemas additionally to dublin-core.
- `handle`: The handle of the object, if existing.

<a id="saf.DSpace.DSpace.add_dc_value"></a>

#### add\_dc\_value

```python
def add_dc_value(element: str,
                 value: str,
                 qualifier: str = 'none',
                 language: str = None)
```

Creates a new dc- metadata field with the given value.

**Arguments**:

- `element`: Type of the metadata-field. For example 'title'.
- `value`: The value of the metadata-field.
- `qualifier`: The qualifier of the field. Default: None
- `language`: The language of the metadata field. Default: None.

<a id="saf.DSpace.DSpace.add_metadata"></a>

#### add\_metadata

```python
def add_metadata(element: str,
                 value: str,
                 prefix: str,
                 qualifier: str = 'none',
                 language: str = None)
```

Creates a new metadata field with the given value. The schema is specified through the prefix parameter.

**Arguments**:

- `element`: Type of the metadata-field. For example 'title'.
- `value`: The value of the metadata-field.
- `prefix`: The prefix of the schema, which should be used.
- `qualifier`: The qualifier of the field. Default: None
- `language`: The language of the metadata field.

<a id="saf.DSpace.DSpace.add_relation"></a>

#### add\_relation

```python
def add_relation(relation_type: str, handle: str)
```

Creates a new relationship to the item.

**Arguments**:

- `relation_type`: The name of the relationship.
- `handle`: The identifier of the related object.

<a id="saf.DSpace.DSpace.add_content"></a>

#### add\_content

```python
def add_content(content_file: str,
                path: str,
                description: str = '',
                width: int = 0,
                server: str = '')
```

Adds additional content-files to the item.

**Arguments**:

- `content_file`: The name of the document, which should be added.
- `path`: The path where to find the document.
- `description`: A description of the content file.
- `width`: The width of an image. Only needed, if the file is a jpg, wich should be reduced.
- `server`: Contains the name of the server on which the image is stored, if so. Stays empty in case of a
local image.

<a id="saf.DSpace.DSpace.dc_schema"></a>

#### dc\_schema

```python
def dc_schema() -> str
```

Creates the content of the file dublin_core.xml

**Returns**:

Ein String im xml-Format.

<a id="saf.DSpace.DSpace.prefix_schema"></a>

#### prefix\_schema

```python
def prefix_schema(prefix: str) -> str
```

Creates the content of the files metadata_[prefix].xml

**Arguments**:

- `prefix`: The prefix of the schema which should be created.

<a id="saf.DSpace.DSpace.create_dir"></a>

#### create\_dir

```python
def create_dir(overwrite: bool = False)
```

Creates the item in folder named 'archive_directory'. If the folder doesn't exist yet. It will be created.

**Arguments**:

- `overwrite`: If true, it overwrites the currently existing files.

<a id="saf.DSpace.DSpace.__len__"></a>

#### \_\_len\_\_

```python
def __len__() -> int
```

Counts the number of metadata fields for the given item.

**Returns**:

The number as an integer value.

<a id="saf.ContentFile"></a>

# saf.ContentFile

<a id="saf.ContentFile.ContentFile"></a>

## ContentFile Objects

```python
class ContentFile()
```

A class for managing content files in the saf-packages.

<a id="saf.ContentFile.ContentFile.__init__"></a>

#### \_\_init\_\_

```python
def __init__(content_type: str,
             name: str,
             path: str,
             content: str | bytes = '',
             show: bool = True)
```

Creates a new ContentFile object.

**Arguments**:

- `content_type`: The type of content file. Must be one off: ('relations', 'licenses', 'images', 'contents',
'handle', 'other')
- `name`: The name of the bitstream.
- `path`: The path, where the file is currently stored.
- `content`: The content of the file, if it shouldn't be loaded from the system.
- `show`: If the bitstream should be listed in the saf-contentfile. Default: True - if the type is relations
or handle the default is False.

<a id="saf.ContentFile.ContentFile.add_description"></a>

#### add\_description

```python
def add_description(description)
```

Creates a description to the content-file.

**Arguments**:

- `description`: String which provides the description..

<a id="saf.ContentFile.ContentFile.add_permission"></a>

#### add\_permission

```python
def add_permission(rw: str, group_name: str)
```

Add access information to the ContentFile.

**Arguments**:

- `rw`: Access-type r-read, w-write.
- `group_name`: Group to which the access will be provided.

<a id="saf.ContentFile.ContentFile.add_iiif"></a>

#### add\_iiif

```python
def add_iiif(label: str, toc: str, w: int = 0)
```

Add, if necessary IIIF-information for the bitstream.

**Arguments**:

- `label`: is the label that will be used for the image in the viewer.
- `toc`: is the label that will be used for a table of contents entry in the viewer.
- `w`: is the image width to reduce it. Default 0

<a id="saf.ContentFile.ContentFile.create_file"></a>

#### create\_file

```python
def create_file(path: str)
```

Creates the need bitstream-file in the archive-directory based on the path information.

**Arguments**:

- `path`: The path, where the bitstream shall be saved.

