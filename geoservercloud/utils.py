EPSG_BBOX = {
    2056: {
        "nativeBoundingBox": {
            "crs": {"$": "EPSG:2056", "@class": "projected"},
            "maxx": 2837016.9329778464,
            "maxy": 1299782.763494124,
            "minx": 2485014.052451379,
            "miny": 1074188.6943776933,
        },
        "latLonBoundingBox": {
            "crs": "EPSG:4326",
            "maxx": 10.603307860867739,
            "maxy": 47.8485348773655,
            "minx": 5.902662003204146,
            "miny": 45.7779277267225,
        },
    },
    4326: {
        "nativeBoundingBox": {
            "crs": {"$": "EPSG:4326", "@class": "projected"},
            "maxx": 180,
            "maxy": 90,
            "minx": -180,
            "miny": -90,
        },
        "latLonBoundingBox": {
            "crs": "EPSG:4326",
            "maxx": 180,
            "maxy": 90,
            "minx": -180,
            "miny": -90,
        },
    },
}


def java_binding(data_type: str) -> str:
    match data_type:
        case "string":
            return "java.lang.String"
        case "integer":
            return "java.lang.Integer"
        case "float":
            return "java.lang.Float"
        case "datetime":
            return "java.sql.Timestamp"
        case "Point":
            return "org.locationtech.jts.geom.Point"
        case "Line":
            return "org.locationtech.jts.geom.LineString"
        case "Polygon":
            return "org.locationtech.jts.geom.Polygon"
        case "MultiPolygon":
            return "org.locationtech.jts.geom.MultiPolygon"
        case _:
            return "java.lang.String"


def convert_attributes(attributes: dict) -> list[dict]:
    geoserver_attributes = []
    for name, data in attributes.items():
        required: bool = data.get("required", False)
        geoserver_attributes.append(
            {
                "name": name,
                "minOccurs": int(required),
                "maxOccurs": 1,
                "nillable": not required,
                "binding": java_binding(data["type"]),
            }
        )
    return geoserver_attributes
