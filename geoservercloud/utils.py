def java_binding(data_type: str) -> str:
    match data_type:
        case "string":
            return "java.lang.String"
        case "integer":
            return "java.lang.Integer"
        case "float":
            return "java.lang.Float"
        case "datetime":
            return "java.util.Date"
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
