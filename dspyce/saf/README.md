# Table of Contents

* [saf](#saf)
  * [export\_relations](#saf.export_relations)
  * [create\_bitstreams](#saf.create_bitstreams)
  * [create\_saf\_package](#saf.create_saf_package)

<a id="saf"></a>

# saf

Module for creating saf packages for DSpace item-imports and -updates.

<a id="saf.export_relations"></a>

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

<a id="saf.create_bitstreams"></a>

#### create\_bitstreams

```python
def create_bitstreams(bitstreams: list[Bitstream], save_path: str)
```

Creates the need bitstream-files in the archive-directory based on the path information.

**Arguments**:

- `bitstreams`: A list of bitstreams to create the files from.
- `save_path`: The path, where the bitstream shall be saved.

<a id="saf.create_saf_package"></a>

#### create\_saf\_package

```python
def create_saf_package(item: Item,
                       element_id: int,
                       path: str,
                       overwrite: bool = False)
```

Creates a saf package folder for an item object.

**Arguments**:

- `item`: The Item to create the package of.
- `element_id`: An id added to the directory name, aka item_<element_id>
- `path`: The path where to store all package files.
- `overwrite`: If true, it overwrites the currently existing files.

