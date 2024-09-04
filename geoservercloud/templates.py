from typing import Any

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


class Templates:

    @staticmethod
    def workspace_wms(workspace: str) -> dict[str, dict[str, Any]]:
        return {
            "wms": {
                "workspace": {"name": workspace},
                "enabled": True,
                "name": "WMS",
                "versions": {
                    "org.geotools.util.Version": [
                        {"version": "1.1.1"},
                        {"version": "1.3.0"},
                    ]
                },
                "citeCompliant": False,
                "schemaBaseURL": "http://schemas.opengis.net",
                "verbose": False,
                "bboxForEachCRS": False,
                "watermark": {
                    "enabled": False,
                    "position": "BOT_RIGHT",
                    "transparency": 100,
                },
                "interpolation": "Nearest",
                "getFeatureInfoMimeTypeCheckingEnabled": False,
                "getMapMimeTypeCheckingEnabled": False,
                "dynamicStylingDisabled": False,
                "featuresReprojectionDisabled": False,
                "maxBuffer": 0,
                "maxRequestMemory": 0,
                "maxRenderingTime": 0,
                "maxRenderingErrors": 0,
                "maxRequestedDimensionValues": 100,
                "cacheConfiguration": {
                    "enabled": False,
                    "maxEntries": 1000,
                    "maxEntrySize": 51200,
                },
                "remoteStyleMaxRequestTime": 60000,
                "remoteStyleTimeout": 30000,
                "defaultGroupStyleEnabled": True,
                "transformFeatureInfoDisabled": False,
                "autoEscapeTemplateValues": False,
            }
        }

    @staticmethod
    def postgis_data_store(
        datastore: str,
        pg_host: str,
        pg_port: int,
        pg_db: str,
        pg_user: str,
        pg_password: str,
        namespace: str,
        pg_schema: str = "public",
    ) -> dict[str, dict[str, Any]]:
        return {
            "dataStore": {
                "name": datastore,
                "connectionParameters": {
                    "entry": [
                        {"@key": "dbtype", "$": "postgis"},
                        {"@key": "host", "$": pg_host},
                        {"@key": "port", "$": pg_port},
                        {"@key": "database", "$": pg_db},
                        {"@key": "user", "$": pg_user},
                        {"@key": "passwd", "$": pg_password},
                        {"@key": "schema", "$": pg_schema},
                        {
                            "@key": "namespace",
                            "$": namespace,
                        },
                        {"@key": "Expose primary keys", "$": "true"},
                    ]
                },
            }
        }

    @staticmethod
    def postgis_jndi_data_store(
        datastore: str,
        jndi_reference: str,
        namespace: str,
        pg_schema: str = "public",
        description: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        return {
            "dataStore": {
                "name": datastore,
                "description": description,
                "connectionParameters": {
                    "entry": [
                        {"@key": "dbtype", "$": "postgis"},
                        {
                            "@key": "jndiReferenceName",
                            "$": jndi_reference,
                        },
                        {
                            "@key": "schema",
                            "$": pg_schema,
                        },
                        {
                            "@key": "namespace",
                            "$": namespace,
                        },
                        {"@key": "Expose primary keys", "$": "true"},
                    ]
                },
            }
        }

    @staticmethod
    def wmts_store(
        workspace: str, name: str, capabilities: str
    ) -> dict[str, dict[str, Any]]:
        return {
            "wmtsStore": {
                "name": name,
                "type": "WMTS",
                "capabilitiesURL": capabilities,
                "workspace": {"name": workspace},
                "enabled": True,
                "metadata": {"entry": {"@key": "useConnectionPooling", "text": True}},
            }
        }

    @staticmethod
    def geom_point_attribute() -> dict[str, Any]:
        return {
            "geom": {
                "type": "Point",
                "required": True,
            }
        }

    @staticmethod
    def feature_type(
        layer: str,
        workspace: str,
        datastore: str,
        attributes: list[dict],
        epsg: int = 4326,
    ) -> dict[str, dict[str, Any]]:
        return {
            "featureType": {
                "name": layer,
                "nativeName": layer,
                "srs": f"EPSG:{epsg}",
                "enabled": True,
                "store": {
                    "name": f"{workspace}:{datastore}",
                },
                "attributes": {
                    "attribute": attributes,
                },
                "nativeBoundingBox": {
                    "crs": EPSG_BBOX[epsg]["nativeBoundingBox"]["crs"],
                    "maxx": EPSG_BBOX[epsg]["nativeBoundingBox"]["maxx"],
                    "maxy": EPSG_BBOX[epsg]["nativeBoundingBox"]["maxy"],
                    "minx": EPSG_BBOX[epsg]["nativeBoundingBox"]["minx"],
                    "miny": EPSG_BBOX[epsg]["nativeBoundingBox"]["miny"],
                },
                "latLonBoundingBox": {
                    "crs": EPSG_BBOX[epsg]["latLonBoundingBox"]["crs"],
                    "maxx": EPSG_BBOX[epsg]["latLonBoundingBox"]["maxx"],
                    "maxy": EPSG_BBOX[epsg]["latLonBoundingBox"]["maxy"],
                    "minx": EPSG_BBOX[epsg]["latLonBoundingBox"]["minx"],
                    "miny": EPSG_BBOX[epsg]["latLonBoundingBox"]["miny"],
                },
            }
        }

    @staticmethod
    def layer_group(
        group: str,
        layers: list[str],
        workspace: str,
        title: str | dict[str, Any],
        abstract: str | dict[str, Any],
        epsg: int = 4326,
        mode: str = "SINGLE",
    ) -> dict[str, dict[str, Any]]:
        modes = ["SINGLE", "OPAQUE_CONTAINER", "NAMED", "CONTAINER", "EO"]
        if not mode in modes:
            raise ValueError(f"Invalid mode: {mode}, possible values are: {modes}")
        template = {
            "layerGroup": {
                "name": group,
                "workspace": {"name": workspace},
                "mode": mode,
                "publishables": {
                    "published": [
                        {"@type": "layer", "name": f"{workspace}:{layer}"}
                        for layer in layers
                    ]
                },
                "styles": {"style": [{"name": ""}] * len(layers)},
                "bounds": {
                    "minx": EPSG_BBOX[epsg]["nativeBoundingBox"]["minx"],
                    "maxx": EPSG_BBOX[epsg]["nativeBoundingBox"]["maxx"],
                    "miny": EPSG_BBOX[epsg]["nativeBoundingBox"]["miny"],
                    "maxy": EPSG_BBOX[epsg]["nativeBoundingBox"]["maxy"],
                    "crs": f"EPSG:{epsg}",
                },
                "enabled": True,
                "advertised": True,
            }
        }
        if title:
            if type(title) is dict:
                template["layerGroup"]["internationalTitle"] = title
            else:
                template["layerGroup"]["title"] = title
        if abstract:
            if type(abstract) is dict:
                template["layerGroup"]["internationalAbstract"] = abstract
            else:
                template["layerGroup"]["abstract"] = abstract
        return template

    @staticmethod
    def wmts_layer(
        name: str,
        native_name: str,
        epsg: int = 4326,
        wgs84_bbox: tuple[float, float, float, float] | None = None,
    ) -> dict[str, dict[str, Any]]:
        template = {
            "wmtsLayer": {
                "advertised": True,
                "enabled": True,
                "name": name,
                "nativeName": native_name,
                "projectionPolicy": "FORCE_DECLARED",
                "serviceConfiguration": False,
                "simpleConversionEnabled": False,
                "srs": f"EPSG:{epsg}",
            }
        }
        if wgs84_bbox:
            template["wmtsLayer"]["latLonBoundingBox"] = {
                "crs": "EPSG:4326",
                "minx": wgs84_bbox[0],
                "maxx": wgs84_bbox[2],
                "miny": wgs84_bbox[1],
                "maxy": wgs84_bbox[3],
            }
            if epsg == 4326:
                template["wmtsLayer"]["nativeBoundingBox"] = {
                    "crs": "EPSG:4326",
                    "minx": wgs84_bbox[0],
                    "maxx": wgs84_bbox[2],
                    "miny": wgs84_bbox[1],
                    "maxy": wgs84_bbox[3],
                }
        return template

    @staticmethod
    def gwc_layer(
        workspace: str, layer: str, gridset: str
    ) -> dict[str, dict[str, Any]]:
        return {
            "GeoServerLayer": {
                "name": f"{workspace}:{layer}",
                "enabled": "true",
                "gridSubsets": {"gridSubset": [{"gridSetName": gridset}]},
            }
        }
