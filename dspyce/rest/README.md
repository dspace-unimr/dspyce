# dspyce.rest
## Package contents:
1. [RestAPI](#restapi)
2. [console](#console)
## Package documentation
### RestAPI
```
class RestAPI(builtins.object)
 |  RestAPI(api_endpoint: str, username: str = None, password: str = None)
 |  
 |  Methods defined here:
 |  
 |  __init__(self, api_endpoint: str, username: str = None, password: str = None)
 |      Creates a new object of the RestAPI class using
 |  
 |  add_bitstream(self, bitstream: dspyce.bitstreams.Bitstream.ContentFile, bundle: dspyce.bitstreams.Bundle.Bundle) -> str
 |      Creates a new bitstream in a given dspace bundle.
 |      :param bitstream: The bitstream to upload.
 |      :param bundle: The bundle to upload the item in.
 |      :return: The uuid of the newly created bitstream.
 |  
 |  add_bundle(self, bundle: dspyce.bitstreams.Bundle.Bundle, item_uuid: str) -> dspyce.bitstreams.Bundle.Bundle
 |      Creates a new bundle based on a given bundle Object in DSpace and returns the created object.
 |      :param bundle: The bundle object to create.
 |      :param item_uuid: The uuid_of the item to create the bundle for.
 |      :return: The newly created object returned from DSpace.
 |  
 |  add_collection(self, collection: dspyce.Collection.Collection, create_tree: bool = False) -> dspyce.Collection.Collection
 |      Creates a new collection in the DSpace instance and its owning communities if create_tree is True.
 |      
 |      :param collection: The collection object to create in DSpace.
 |      :param create_tree: If the owning communities shall be created as well.
 |      :return: Returns the newly created Collection.
 |  
 |  add_community(self, community: dspyce.Community.Community | dspyce.DSpaceObject.DSpaceObject, create_tree: bool = False) -> dspyce.Community.Community
 |      Creates a new community in the DSpace instance and its owning community if create_tree is True.
 |      
 |      :param community: The collection object to create in DSpace.
 |      :param create_tree: If the owning communities shall be created as well.
 |      :return: Returns the newly created Community.
 |  
 |  add_item(self, item: dspyce.Item.Item, create_tree: bool = False) -> dspyce.Item.Item
 |      Adds an item object to DSpace including files and relations. Based on the add_object method.
 |      
 |      :param item: The item to push into DSpace.
 |      :param create_tree: Creates the owning collections and communities above this item if not yet existing.
 |      :return: An item object including the new uuid.
 |  
 |  add_metadata(self, metadata: list[dspyce.metadata.MetaData.MetaData] | dict[str, list[dict]], object_uuid: str, obj_type: str) -> dspyce.DSpaceObject.DSpaceObject
 |      Add a new metadata value information to a DSpace object, identified by its uuid.
 |      
 |      :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
 |      {<tag> : [{"value": <value>, "language": <language>...}]}
 |      :param object_uuid: The uuid of the object to add the metadata to.
 |      :param obj_type: The type of DSpace object. Must be one of item, collection or community.
 |      :return: The updated DSpace object.
 |      :raises ValueError: If a not existing objectType is used.
 |  
 |  add_object(self, obj: dspyce.DSpaceObject.DSpaceObject) -> dspyce.DSpaceObject.DSpaceObject | dspyce.Collection.Collection | dspyce.Item.Item | dspyce.Community.Community
 |      Creates a new object in the DSpace Instance.
 |      
 |      :param obj: The object to create.
 |      :return: The newly created object.
 |  
 |  add_relationship(self, relation: dspyce.Relation.Relation) -> dict
 |      Creates a new relationship between to items based on the information in the Relation object.
 |      
 |      :param relation: The relation to create.
 |  
 |  authenticate_api(self) -> bool
 |      Authenticates to the REST-API
 |      
 |      :return: True, if the authentication worked.
 |  
 |  delete_bitstream(self, bitstream_uuid: str | list[str])
 |      Permanently removes a bitstream of a list of bitstreams from the repository. Handle be carefully when using the
 |      method, there won't be a confirmation step.
 |      
 |      :param bitstream_uuid: The uuid of the bitstream to delete
 |  
 |  delete_metadata(self, tag: str | list[str], object_uuid: str, obj_type: str, position: int | str = -1) -> dspyce.DSpaceObject.DSpaceObject
 |      Deletes a specific metadata-field or value of a DSpace Item. Can delete a list of fields as well as only one.
 |      
 |      :param tag: A tag or list of tags wich shall be deleted.
 |      :param object_uuid: The uuid of the DSpace Item to delete the metadata from.
 |      :param position: The position of the metadata value to delete. Can only be used, if only one tag is provided.
 |      :param obj_type: The type of DSpace object. Must be one of item, collection or community.
 |      :return: The updated DSpace object.
 |      :raises ValueError: If a not existing objectType is used. Or a position is given, when tag is a list.
 |  
 |  get_api(self, endpoint: str, params: dict = None) -> dict | None
 |      Performs a get request to the api based on a given string endpoint returns the JSON response if successfully.
 |      
 |      :param endpoint: The endpoint information: aka https://self.api_endpoint/<endpoint>
 |      :param params: A list of additional parameters to pass to the endpoint.
 |      :return: The json response as a dict.
 |  
 |  get_dso(self, uuid: str, endpoint: str) -> dspyce.DSpaceObject.DSpaceObject | dspyce.Item.Item | dspyce.Collection.Collection | dspyce.Community.Community
 |      Retrieves a DSpace object from the api based on its uuid and the endpoint information.
 |      
 |      :param uuid: The uuid of the object.
 |      :param endpoint: The endpoint string. Must be one of ('items', 'collections', 'communities')
 |      :return: Returns a DSpace object
 |  
|  get_item(self, uuid: str, get_related: bool = True, get_bitstreams: bool = True, pre_downloaded_item: dspyce.Item.Item = None) -> dspyce.Item.Item | None
 |      Retrieves a DSpace-Item by its uuid from the API.
 |      
 |      :param uuid: The uuid of the item to get.
 |      :param get_related: If true, also retrieves related items from the API.
 |      :param get_bitstreams: If true, also retrieves bitstreams of the item from the API.
 |      :param pre_downloaded_item: If a pre downloaded item is provided (aka blank dso), then only additional
 |      information such as relationships, owning collection, bundles and bitstreams will be provided.
 |      :return: An object of the class Item.
 |  
 |  get_item_bitstreams(self, item_uuid: str) -> list[dspyce.bitstreams.Bitstream.Bitstream]
 |      Retrieves the bitstreams connected to a DSpace Object. And returns them as a list.
 |      
 |      :param item_uuid: The uuid of the item to retrieve the bitstreams from.
 |      :return: A list of Bitstream objects.
 |  
 |  get_item_bundles(self, item_uuid: str) -> list[dspyce.bitstreams.Bundle.Bundle]
 |      Retrieves the bundles connected to a DSpaceObject and returns them as list.
 |      
 |      :param item_uuid: The uuid of the item to retrieve the bundles from.
 |      :return: The list of Bundle objects.
 |  
 |  get_item_collections(self, item_uuid: str) -> list[dspyce.Collection.Collection]
 |      Retrieves a list of collections from the REST-API based on the uuid of an item. The first will be the owning
 |      collection.
 |      
 |      :param item_uuid: The uuid of the item.
 |  
 |  get_item_relationships(self, item_uuid: str) -> list[dspyce.Relation.Relation]
 |      Retrieves a list of relationships of DSpace entity from the api.
 |      
 |      :param item_uuid: The uuid of the item to retrieve the relationships for.
 |      :return: A list of relation objects.
 |  
 |  get_items_in_scope(self, scope_uuid: str, query: str = '', size: int = -1, page: int = -1, full_item: bool = False) -> list[dspyce.Item.Item]
 |      Returns a list of DSpace items in a given collection or community. Can be further reduced by query parameter.
 |      
 |      :param scope_uuid: The uuid of the collection to retrieve the items from.
 |      :param query: Additional query parameters for the request.
 |      :param size: The number of objects per page. Use -1 to select the default.
 |      :param page: The page to retrieve if a paginated list is returned. Use -1 to retrieve all.
 |      :param full_item: If the full item information should be downloaded (Including relationships, bundles and
 |      bitstreams. This can be slower due to additional api calls).
 |      :return: A list of Item objects.
 |  
|  get_metadata_field(self, schema: str = '', element: str = '', qualifier: str = '', field_id: int = -1) -> list[dict]
 |      Checks if given metadata field exists in the DSpace instance. Returns one or more found metadata fields in a
 |      list of dict.
 |      
 |      :param schema: The schema of the field, if empty this field won't be taken in account for the search request.
 |      :param element: The element of the field, if empty this field won't be taken in account for the search request.
 |      :param qualifier: The qualifier of the field, if empty this field won't be taken in account for the search
 |      request.
 |      :param field_id: The exact metadata field id to look for. If the correct fields is already known.
 |      :return: A list of dictionaries in the following form: {id: <id>, element: <element>, qualifier: <qualifier>,
 |      scopeNote: <scopeNote>, schema: {id: <schema-id>, prefix: <prefix>, namespace: <namespace>}
 |  
 |  get_paginated_objects(self, endpoint: str, object_key: str, query_params: dict = None, page: int = -1, size: int = 20) -> list[dict]
 |      Retrieves a paginated list of objects from the remote dspace endpoint and returns them as a list.
 |      
 |      :param endpoint: The endpoint to retrieve the objects from.
 |      :param object_key: The dict key to get the object list from the json-response. For example "bundles" or
 |      "bitstreams"
 |      :param query_params: Additional query parameters to add to the request.
 |      :param page: The page number to retrieve. Must be set to -1 to retrieve all pages. Default -1.
 |      :param size: The page size, aka the number of objects per page.
 |      :return: The list of retrieved objects.
 |  
 |  get_parent_community(self, dso: dspyce.Collection.Collection | dspyce.Community.Community) -> dspyce.Community.Community | None
 |      Retrieves the parent community of a given collection or Community.
 |      
 |      :param dso: The object to get the parent community from. Must be either Collection or Community
 |  
 |  get_relations_by_type(self, entity_type: str) -> list[dspyce.Relation.Relation]
 |      Parses the REST API and returns a list of relationships, which have the given entity on the left or right side.
 |      
 |      :param entity_type: The entity_type to look for.
 |      :return: Return s a list of relations.
 |  
 |  patch_api(self, url: str, json_data: list, params: dict = None) -> dict | None
 |      Sends a patch request to the api in order to update, add or remove metadata information.
 |      
 |      :param url: The url of the api, where to replace the metadata.
 |      :param json_data: The data object containing action information.
 |      :param params: Additional params for the operation.
 |      :return: The JSON response of the server, if the operation was successfull.
 |      :raise RequestException: If the JSON response doesn't have the status code 200 or 201
 |  
 |  post_api(self, url: str, json_data: dict, params: dict) -> dict
 |
 |  replace_metadata(self, metadata: dspyce.metadata.MetaData.MetaData | dict[str, list[dict] | dict], object_uuid: str, obj_type: str, position: int = -1) -> dspyce.DSpaceObject.DSpaceObject
 |      Add a new metadata value information to a DSpace object, identified by its uuid.
 |      
 |      :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
 |      {<tag> : [{"value": <value>, "language": <language>...}]}
 |      :param object_uuid: The uuid of the object to add the metadata to.
 |      :param obj_type: The type of DSpace object. Must be one of item, collection or community.
 |      :param position: The position of the metadata value to replace.
 |      :return: The updated DSpace object.
 |      :raises ValueError: If a not existing objectType is used.
 |  
 |  search_items(self, query_params: dict = None, size: int = 20, full_item: bool = False) -> list[dspyce.DSpaceObject.DSpaceObject]
 |      Search items via rest-API using solr-base query parameters. Uses the endpoint /discover/search/objects. If no
 |      query_params are provided, the whole repository will be retrieved.
 |      
 |      :param query_params: A dictionary with query parameters to filter the search results.
 |      :param size: The number of objects to retrieve per page.
 |      :param full_item: If the full items (including relations and bitstreams) shall be downloaded or not.
 |      Default false.
 |      :return: The list of found DSpace objects.
 |  
 |  update_csrf_token(self, req: requests.models.Request | requests.models.Response)
 |      Update the csrf_token based on the current requests.
 |      
 |      :param req: The current request to check the token from.
 |  
 |  update_metadata(self, metadata: dict[str, list[dict] | dict[str, dict]], object_uuid: str, obj_type: str, operation: str, position: int = -1) -> dspyce.DSpaceObject.DSpaceObject
 |      Update a new metadata value information to a DSpace object, identified by its uuid.
 |      
 |      :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
 |      {<tag> : [{"value": <value>, "language": <language>...}]}. May also contain position information. For "remove"-
 |      operation the form must be {<tag>: [{postion: <position>}] | []}
 |      :param object_uuid: The uuid of the object to add the metadata to.
 |      :param obj_type: The type of DSpace object. Must be one of item, collection or community
 |      :param operation: The selected update operation. Must be one off (add, replace, remove).
 |      :param position: The position of the metadata value to add. Only possible if metadata is of type dict[dict[]]
 |      :return: The updated DSpace object.
 |      :raises ValueError: If a not existing objectType is used or wrong operation type.
```
### console
```
module dspyce.rest.console in dspyce.rest:
NAME
    dspyce.rest.console
FUNCTIONS
    authenticate_to_rest(rest_api: str) -> dspyce.rest.RestAPI.RestAPI
        Connect to a given REST-API and ask for username and password via commandline.
        
        :param rest_api: The url of the REST-API endpoint.
        :return: An object of the class Rest.
```