from typing import Any

from geoservercloud.utils import EPSG_BBOX


class Templates:
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
        international_title: dict[str, str] | None = None,
        international_abstract: dict[str, str] | None = None,
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
        if international_title:
            template["wmtsLayer"]["internationalTitle"] = international_title
        if international_abstract:
            template["wmtsLayer"]["internationalAbstract"] = international_abstract
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
