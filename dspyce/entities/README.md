# *entity* package

Python package for analysing and working with entity modells in DSpace.
This package is mostly used for drawing entity graphs based on the
relationship-types.xml or a REST endpoint.

## Quickstart:
To draw a modell based on a given RestAPI:
```python
import dspyce as ds

ds.entities.from_rest_api('https://sandbox.dspace.org/server/api').draw_graph()
```
You can check if a DSpace-repository uses entities by running:
```python
import dspyce as ds

ds.entities.check_entities_rest('https://sandbox.dspace.org/server/api')
```

## Overview

### class *EntityModel*:
The EntityModell class provides methods and attributes to work with entity modells.
An object of this class represents entities and relationships of a DSpace repository.

You can draw an entity modell by calling the draw() method of an *EntityModell* object.

### Generating an *EntityModell* object
Beside creating an *EntityModell* manually based on the class methods, you can import
an existing modell based on a given RestAPI or the [dspace]/config/entities/relationship-types.xml file.

**RestAPI**: `dspyce.entities.from_rest_api('https://sandbox.dspace.org/server/api')`
**relationship-types.xml**: `dspyce.entities.from_relationship_file('[dspace]/config/entities/relationship-types.xml')`
