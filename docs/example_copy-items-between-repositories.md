# Example use case _dspyce_: Copying items between two DSpace repositories

A common scenario for the use of the dspyce script might be copying serveral dspyce items from one DSpace repository to
another one.

To achieve this, at first you must download the items from the _old_ repository:
```python
import dspyce as ds

old_rest = ds.rest.RestAPI('https://demo.dspace.org/server/api', workers=10)
item_uuids = []
scope_uuids = []

items = []
for i in item_uuids:
    items.append(ds.Item.get_from_rest(old_rest, i))

for s in scope_uuids:
    items_in_scope = old_rest.get_objects_in_scope(s, get_bitstreams=True)
    # Reduce list to items, because get_objects_in_scope() method retrieves all DSpace objects from a given scope.
    items_in_scope = list(filter(lambda x: isinstance(x, ds.Item), items_in_scope))
    items += items_in_scope
```
Now, all items from a given list of scope uuids and or item uuids are pulled from the Rest API. If you want to add those
to another DSpace repository you must remove handle, uuids and owning collections because those are specific to the old
repository. There is currently no way to set handles via the RestAPI.
```python
for i in items:
    i.uuid = ''
    i.handle = ''
    i.collections = ''
```
Now you can connect to the RestAPI of the new repository and add the items.
```python
new_rest = ds.rest.authenticate_to_rest('https://sandbox.dspace.org/server/api')
# You must set the uuid of the new owning collection.
UUID_OWNING_COLLECTION = ''
owning_collection = ds.Collection.get_from_rest(new_rest, UUID_OWNING_COLLECTION)
for i in items:
    i.add_collection(owning_collection, True)
    i.to_rest(new_rest)
```
Now all items and there bitstreams should be uploaded to the new DSpace repository. 