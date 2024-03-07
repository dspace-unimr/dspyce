from ..rest import RestAPI
from ..DSpaceObject import DSpaceObject

REPORT_TYPES: tuple = ('TotalVisits', 'TotalVisitsPerMonth', 'TotalDownloads', 'TopCountries', 'TopCities')
"""The allowed report_type values."""


def get_point_views(point: dict) -> int | None:
    """
    Return the views value from a point dict, retrieved by the RestAPI of DSpace instance.

    :param point: The dictionary contain the points' data.
    :return: The views value, if existing, else None.
    :raises TypeError: If the parameter point is not form type dict.
    """
    if not isinstance(point, dict):
        raise TypeError(f'The parameter point must be a dictionary! But found: {type(point)}')
    if isinstance(point.get('values'), dict) and 'views' in point['values'].keys():
        return point['values']['views']

    return None


def download_statistics_to_object(object_uuid: str, report_type: str, rest_api: RestAPI) -> dict | None:
    """
    Retrieves a statistics report from a given RestAPI endpoint connected to the given object_id.

    :param object_uuid: The uuid of the object to get the report from.
    :param report_type: The report type to retrieve. (Must be one of REPORT_TYPES)
    :param rest_api: A given rest API to retrieve the data from.
    :return: The report as a dict object containing the information.
    :raise ValueError: If the report type is incorrect.
    """
    if report_type not in REPORT_TYPES:
        raise ValueError(f'The report_type must be one of {REPORT_TYPES}, but got "{report_type}"')
    request_id = f'{object_uuid}_{report_type}'
    json_resp = rest_api.get_api(f'statistics/usagereports/{request_id}')
    if json_resp is None:
        return None
    if 'points' not in json_resp.keys() or len(json_resp['points']) <= 0:
        return None
    match report_type:
        case 'TotalVisits':
            return {report_type: get_point_views(json_resp['points'][0])}
        case 'TotalDownloads':
            downloads = []
            for p in json_resp['points']:
                downloads.append({'uuid': p['id'], 'label': p['label'], 'downloads': get_point_views(p)})
            return {report_type: downloads}
        case 'TotalVisitsPerMonth':
            return {report_type: {p['label']: get_point_views(p) for p in json_resp['points']}}
    return None


def download_statistics(object_list: list[str] | list[DSpaceObject], report_type: str,
                        rest_api: RestAPI) -> list[dict] | list[DSpaceObject]:
    """
    Retrieves statistic reports for list of DSpaceObject base on their uuids. Adds the reports directly to the objects
    if a list of DSpaceObjects is provided.

    :param object_list: A list of object uuids or DSpaceObject objects to retrieve the data for.
    :param report_type: The type of report to retrieve.
    :param rest_api: The rest_api to retrieve the statistics from.
    :return: A list of Report objects, if object_list is a list of uuids, else: returns a list of DSpaceObjects with
    added statistics.
    """
    if len(object_list) > 0 and isinstance(object_list[0], str):
        return [download_statistics_to_object(str(o), report_type, rest_api) for o in object_list]

    for o in object_list:
        o: DSpaceObject
        tmp = download_statistics_to_object(o.uuid, report_type, rest_api)
        o.add_statistic_report(tmp)
        del tmp
    return object_list


def all_statistics_to_object(obj: str | DSpaceObject, rest_api: RestAPI) -> list[dict] | DSpaceObject:
    """
    Returns all currently available reports for an object as a list or the updated DSpaceObject object if the object
    parameter is of type DSpaceObject.

    :param obj: The uuid of the object to get the report from or the corresponding DSpaceObject.
    :param rest_api: A given rest API to retrieve the data from.
    :return: A Report object containing the information.
    :raise TypeError: If type(object) is not DSpaceObject
    """
    if isinstance(obj, DSpaceObject):
        stats = list(filter(lambda x: x is not None,
                            [download_statistics_to_object(obj.uuid,
                                                           report_type, rest_api) for report_type in REPORT_TYPES]))
        obj.add_statistic_report(stats)
        del stats
        return obj
    if isinstance(obj, str):
        return list(filter(lambda x: x is not None,
                           [download_statistics_to_object(obj,
                                                          report_type, rest_api) for report_type in REPORT_TYPES]))

    raise TypeError(f"The obj type must be either DSpaceObject or str, but got {type(obj)}!")


def all_statistics(object_list: list[str] | list[DSpaceObject],
                   rest_api: RestAPI) -> list[dict] | list[DSpaceObject]:
    """
    Retrieves all statistic reports for a given list of DSpaceObject based on their uuids. Adds the reports directly to
    the objects if a list of DSpaceObjects is provided.

    :param object_list: A list of object uuids or DSpaceObject objects to retrieve the data for.
    :param rest_api: The rest_api to retrieve the statistics from.
    :return: A list of Report objects, if object_list is a list of uuids, else: returns a list of DSpaceObjects with
    added statistics.
    """
    if len(object_list) > 0 and isinstance(object_list[0], str):
        reports = []
        for o in object_list:
            o: str
            reports += all_statistics_to_object(o, rest_api)
        return reports

    for o in object_list:
        o: DSpaceObject
        o.add_statistic_report(all_statistics_to_object(o.uuid, rest_api))
    return object_list
