import logging

import jsonschema
import requests

log = logging.getLogger()


class SettingsWFS:
    _responseSchema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "wfs": {
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
                    "gml": {
                        "type": "object",
                        "properties": {
                            "entry": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "version": {"type": "string"},
                                        "gml": {
                                            "type": "object",
                                            "properties": {
                                                "srsNameStyle": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "overrideGMLAttributes": {
                                                    "type": "boolean"
                                                },
                                            },
                                            "required": [
                                                "srsNameStyle",
                                                "overrideGMLAttributes",
                                            ],
                                        },
                                    },
                                    "required": ["version", "gml"],
                                },
                            }
                        },
                        "required": ["entry"],
                    },
                    "serviceLevel": {"type": "string"},
                    "maxFeatures": {"type": "integer"},
                    "featureBounding": {"type": "boolean"},
                    "canonicalSchemaLocation": {"type": "boolean"},
                    "encodeFeatureMember": {"type": "boolean"},
                    "hitsIgnoreMaxFeatures": {"type": "boolean"},
                    "includeWFSRequestDumpFile": {"type": "boolean"},
                    "allowGlobalQueries": {"type": "boolean"},
                    "simpleConversionEnabled": {"type": "boolean"},
                },
                "required": ["workspace", "enabled", "name"],
            }
        },
        "required": ["wfs"],
    }

    def __init__(self, workspace) -> None:
        self.workspace = workspace
        self.wfs = None

    def put_payload(self, enabled=None, title=None, keywords=None):
        payload = {
            "wfs": {
                "workspace": {"name": self.workspace},
                "enabled": enabled,
                "title": title,
                "keywords": {"string": keywords} if keywords else None,
            }
        }
        payload["wfs"] = {k: v for k, v in payload["wfs"].items() if v is not None}
        return payload

    @property
    def responseSchema(self):
        return self._responseSchema

    def endpoint_url(self):
        return f"/services/wfs/workspaces/{self.workspace}/settings.json"

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
            self.wfs = response.json()
            self.validate(self.settingsWFS)
        else:
            log.error(f"Error: {response.status_code}")
