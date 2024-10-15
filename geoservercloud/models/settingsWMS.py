import logging

import jsonschema
import requests

log = logging.getLogger()


class SettingsWMS:
    _responseSchema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "wms": {
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                    "enabled": {"type": "boolean"},
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "maintainer": {"type": "string"},
                    "abstract": {"type": "string"},
                    "accessConstraints": {"type": "string"},
                    "fees": {"type": "string"},
                    "versions": {
                        "type": "object",
                        "properties": {
                            "org.geotools.util.Version": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {"version": {"type": "string"}},
                                    "required": ["version"],
                                },
                            }
                        },
                        "required": ["org.geotools.util.Version"],
                    },
                    "keywords": {
                        "type": "object",
                        "properties": {
                            "string": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["string"],
                    },
                    "citeCompliant": {"type": "boolean"},
                    "onlineResource": {"type": "string"},
                    "schemaBaseURL": {"type": "string"},
                    "verbose": {"type": "boolean"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "entry": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "@key": {"type": "string"},
                                        "$": {"type": "string"},
                                    },
                                },
                            }
                        },
                        "required": ["entry"],
                    },
                    "bboxForEachCRS": {"type": "boolean"},
                    "watermark": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "position": {"type": "string"},
                            "transparency": {"type": "integer"},
                        },
                        "required": ["enabled", "position", "transparency"],
                    },
                    "interpolation": {"type": "string"},
                    "getFeatureInfoMimeTypeCheckingEnabled": {"type": "boolean"},
                    "getMapMimeTypeCheckingEnabled": {"type": "boolean"},
                    "dynamicStylingDisabled": {"type": "boolean"},
                    "featuresReprojectionDisabled": {"type": "boolean"},
                    "maxBuffer": {"type": "integer"},
                    "maxRequestMemory": {"type": "integer"},
                    "maxRenderingTime": {"type": "integer"},
                    "maxRenderingErrors": {"type": "integer"},
                    "maxRequestedDimensionValues": {"type": "integer"},
                    "cacheConfiguration": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "maxEntries": {"type": "integer"},
                            "maxEntrySize": {"type": "integer"},
                        },
                        "required": ["enabled", "maxEntries", "maxEntrySize"],
                    },
                    "remoteStyleMaxRequestTime": {"type": "integer"},
                    "remoteStyleTimeout": {"type": "integer"},
                    "defaultGroupStyleEnabled": {"type": "boolean"},
                },
                "required": [],
            }
        },
        "required": ["wms"],
    }

    def __init__(self, workspace="default") -> None:
        self.workspace = workspace
        self.wms = None

    def put_payload(self, enabled=None, title=None, keywords=None):
        payload = {
            "wms": {
                "workspace": {"name": self.workspace},
                "enabled": enabled,
                "title": title,
                "keywords": {"string": keywords} if keywords else None,
            }
        }
        payload["wms"] = {k: v for k, v in payload["wms"].items() if v is not None}
        return payload

    @property
    def responseSchema(self):
        return self._responseSchema

    def endpoint_url(self):
        return f"/services/wms/workspaces/{self.workspace}/settings.json"

    def endpoint_url_default_service(self):
        return f"/services/wms/settings.json"

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
            self.wms = response.json()
            self.validate(self.wms)
        else:
            log.error(f"Error: {response.status_code}")
