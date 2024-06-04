# entities/__init__.py
"""
Python package for analysing and working with entity modells in DSpace.
This package is mostly used for drawing entity graphs based on the relationship-types.xml or a REST endpoint.

To draw an entity modell based on a RestApi, you must run the following code:
>>> from dspyce import entities
>>> entities.from_rest_api('https://sandbox.dspace.org/server/api').draw_graph()
"""
from .models import EntityModell
from .models import from_relationship_file, from_rest_api
from .models import check_entities_rest
