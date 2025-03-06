from geoservercloud.models.wmslayer import WmsLayer


def test_wmslayer_from_get_response_payload():
    mock_response = {
        "wmsLayer": {
            "name": "test_layer_name",
            "nativeName": "test_native_name",
            "namespace": {
                "name": "test_namespace",
                "href": "http://namespace.org",
            },
            "title": "Test Title",
            "description": "Test Description",
            "abstract": "Test Abstract",
            "keywords": {"string": "test_keyword"},
            "nativeCRS": {
                "@class": "projected",
                "$": 'PROJCS["CH1903+ / LV95", \n  GEOGCS["CH1903+", \n    DATUM["CH1903+", \n      SPHEROID["Bessel 1841", 6377397.155, 299.1528128, AUTHORITY["EPSG","7004"]], \n      TOWGS84[674.374, 15.056, 405.346, 0.0, 0.0, 0.0, 0.0], \n      AUTHORITY["EPSG","6150"]], \n    PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]], \n    UNIT["degree", 0.017453292519943295], \n    AXIS["Geodetic longitude", EAST], \n    AXIS["Geodetic latitude", NORTH], \n    AUTHORITY["EPSG","4150"]], \n  PROJECTION["Oblique_Mercator", AUTHORITY["EPSG","9815"]], \n  PARAMETER["longitude_of_center", 7.439583333333333], \n  PARAMETER["latitude_of_center", 46.952405555555565], \n  PARAMETER["azimuth", 90.0], \n  PARAMETER["scale_factor", 1.0], \n  PARAMETER["false_easting", 2600000.0], \n  PARAMETER["false_northing", 1200000.0], \n  PARAMETER["rectified_grid_angle", 90.0], \n  UNIT["m", 1.0], \n  AXIS["Easting", EAST], \n  AXIS["Northing", NORTH], \n  AUTHORITY["EPSG","2056"]]',
            },
            "srs": "EPSG:2056",
            "nativeBoundingBox": {
                "minx": 2100000,
                "maxx": 2850000,
                "miny": 1050000,
                "maxy": 1400000,
                "crs": {"@class": "projected", "$": "EPSG:2056"},
            },
            "latLonBoundingBox": {
                "minx": 0.659866,
                "maxx": 10.835877,
                "miny": 45.419461,
                "maxy": 48.751073,
                "crs": "EPSG:4326",
            },
            "projectionPolicy": "FORCE_DECLARED",
            "enabled": True,
            "store": {
                "@class": "wmsStore",
                "name": "test_workspace:test_store",
                "href": "http://localhost",
            },
            "serviceConfiguration": False,
            "forcedRemoteStyle": "",
            "preferredFormat": "image/png",
            "metadataBBoxRespected": False,
        }
    }

    wms_layer = WmsLayer.from_get_response_payload(mock_response)

    assert wms_layer.namespace_name == "test_namespace"
    assert wms_layer.name == "test_layer_name"
    assert wms_layer.native_name == "test_native_name"
    assert wms_layer.store_name == "test_store"
    assert wms_layer.workspace_name == "test_workspace"
    assert wms_layer.srs == "EPSG:2056"
    assert wms_layer.native_bounding_box == {
        "minx": 2100000,
        "maxx": 2850000,
        "miny": 1050000,
        "maxy": 1400000,
        "crs": {"@class": "projected", "$": "EPSG:2056"},
    }
    assert wms_layer.lat_lon_bounding_box == {
        "minx": 0.659866,
        "maxx": 10.835877,
        "miny": 45.419461,
        "maxy": 48.751073,
        "crs": "EPSG:4326",
    }
    assert wms_layer.title.value == "Test Title"
    assert wms_layer.abstract.value == "Test Abstract"
    assert wms_layer.description == "Test Description"
    assert wms_layer.keywords == ["test_keyword"]
    assert wms_layer.srs == "EPSG:2056"
    assert wms_layer.native_crs == {
        "@class": "projected",
        "$": 'PROJCS["CH1903+ / LV95", \n  GEOGCS["CH1903+", \n    DATUM["CH1903+", \n      SPHEROID["Bessel 1841", 6377397.155, 299.1528128, AUTHORITY["EPSG","7004"]], \n      TOWGS84[674.374, 15.056, 405.346, 0.0, 0.0, 0.0, 0.0], \n      AUTHORITY["EPSG","6150"]], \n    PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]], \n    UNIT["degree", 0.017453292519943295], \n    AXIS["Geodetic longitude", EAST], \n    AXIS["Geodetic latitude", NORTH], \n    AUTHORITY["EPSG","4150"]], \n  PROJECTION["Oblique_Mercator", AUTHORITY["EPSG","9815"]], \n  PARAMETER["longitude_of_center", 7.439583333333333], \n  PARAMETER["latitude_of_center", 46.952405555555565], \n  PARAMETER["azimuth", 90.0], \n  PARAMETER["scale_factor", 1.0], \n  PARAMETER["false_easting", 2600000.0], \n  PARAMETER["false_northing", 1200000.0], \n  PARAMETER["rectified_grid_angle", 90.0], \n  UNIT["m", 1.0], \n  AXIS["Easting", EAST], \n  AXIS["Northing", NORTH], \n  AUTHORITY["EPSG","2056"]]',
    }
    assert wms_layer.service_configuration == False
    assert wms_layer.forced_remote_style == ""
    assert wms_layer.preferred_format == "image/png"
    assert wms_layer.metadata_bbox_respected == False
