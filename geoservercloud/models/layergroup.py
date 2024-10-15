import logging

import jsonschema
import requests

from .Layer import Layer
from .Style import Style

log = logging.getLogger()


class LayerGroup:
    _responseSchema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "layerGroup": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "mode": {"type": "string"},
                    "title": {"type": "string"},
                    "abstractTxt": {"type": "string"},
                    "workspace": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                    "internationalTitle": {"type": "string"},
                    "internationalAbstract": {"type": "string"},
                    "publishables": {
                        "type": "object",
                        "properties": {
                            "published": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "@type": {"type": "string", "const": "layer"},
                                        "name": {"type": "string"},
                                        "href": {"type": "string", "format": "uri"},
                                    },
                                    "required": ["@type", "name", "href"],
                                },
                            }
                        },
                        "required": ["published"],
                    },
                    "styles": {
                        "type": "object",
                        "properties": {
                            "style": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "href": {"type": "string", "format": "uri"},
                                    },
                                    "required": ["name", "href"],
                                },
                            }
                        },
                        "required": ["style"],
                    },
                    "bounds": {
                        "type": "object",
                        "properties": {
                            "minx": {"type": "number"},
                            "maxx": {"type": "number"},
                            "miny": {"type": "number"},
                            "maxy": {"type": "number"},
                            "crs": {
                                "type": "object",
                                "properties": {
                                    "@class": {"type": "string", "const": "projected"},
                                    "$": {"type": "string", "const": "EPSG:25833"},
                                },
                                "required": ["@class", "$"],
                            },
                        },
                        "required": ["minx", "maxx", "miny", "maxy", "crs"],
                    },
                    "dateCreated": {"type": "string", "format": "date-time"},
                },
                "required": [
                    "name",
                    "mode",
                    "title",
                    "abstractTxt",
                    "workspace",
                    "publishables",
                    "styles",
                    "bounds",
                    "dateCreated",
                ],
            }
        },
        "required": ["layerGroup"],
    }

    def __init__(
        self,
        workspace_name,
        layer_group_name,
        layers=[],
        styles=[],
        crs={"@class": "projected", "$": "EPSG:25833"},
        bbox={
            "minx": 269387.6943774796,
            "maxx": 731380.9792889762,
            "miny": 5138491.809334871,
            "maxy": 9330126.130139956,
        },
        internationalTitle={"de-DE": "change-me - title"},
        internationalAbstract={"de-DE": "change-me - abstract"},
        metadataLinksIdentifier="change-me - metadataLinksIdentifier",
        keywords={},
    ) -> None:
        self.workspace = workspace_name
        self.name = layer_group_name
        log.debug(f"LayerGroup: {self.name}")
        log.debug(f"layers = {layers}")
        log.debug(f"layers: {layers[0].toListItem()}")
        self.layers_list_items = self.layerList2layerListItem(layers)
        self.styles_list_items = self.stylesList2styleListItem(styles)
        self.metadataLinksIdentifier = metadataLinksIdentifier
        self.crs = crs
        self.bounds = {
            "minx": bbox["minx"],
            "maxx": bbox["maxx"],
            "miny": bbox["miny"],
            "maxy": bbox["maxy"],
            "crs": self.crs,
        }

        self.keywords = keywords
        self.internationalTitle = internationalTitle
        self.internationalAbstract = internationalAbstract

    @property
    def responseSchema(self):
        return self._responseSchema

    def stylesList2styleListItem(self, stylesList):
        styleListItems = []
        for style in stylesList:
            styleListItems.append(style.toListItem())
        return styleListItems

    def layerList2layerListItem(self, layerList):
        layerListItems = []
        for layer in layerList:
            layerListItems.append(layer.toListItem())
        return layerListItems

    def endpoint_url(self):
        return f"/workspaces/{self.workspace}/layergroups/{self.layerGroupName}.json"

    def post_payload(self):
        payload = {
            "layerGroup": {
                "name": self.name,
                "mode": "SINGLE",
                "workspace": {"name": self.workspace},
                "internationalTitle": self.internationalTitle,
                "internationalAbstract": self.internationalAbstract,
                "publishables": {"published": self.layers_list_items},
                "styles": {"style": self.styles_list_items},
                "metadataLinks": {
                    "metadataLink": {
                        "type": "text/xml",
                        "metadataType": "ISO19115:2003",
                        "content": self.metadataLinksIdentifier,
                    }
                },
                "bounds": self.bounds,
            }
        }

        return payload

    def validate(self, response):
        try:
            jsonschema.validate(response, self.responseSchema)
        except jsonschema.exceptions.ValidationError as err:
            print(err)
            return False
        return True

    def parseResponse(self, response):
        if response.status_code == 200:
            # Parse the JSON response
            self.layerGroup = response.json()
            self.validate(self.layerGroup)
        else:
            log.error(f"Error: {response.status_code}")
