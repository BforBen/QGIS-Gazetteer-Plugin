from json import loads
from collections import namedtuple

url = "https://www2.guildford.gov.uk/services/address/2/lookup/bysomething"
params = {
    'type': 'json',
    'query': '##searchstring##',
	'Scope': 'Local',
	'IncludeHistorical': 'False',
}


def parseRequestResults(data, iface=None):
    json_result = loads(data)
    for item in json_result:
        mapped = dict(item)
        result = namedtuple('Result', ['description', 'x', 'y', 'zoom', 'epsg'])
        result.description = mapped['FullAddress']
        result.x = float(mapped['Easting'])
        result.y = float(mapped['Northing'])
        result.zoom = 1250
        result.epsg = 27700
        yield result