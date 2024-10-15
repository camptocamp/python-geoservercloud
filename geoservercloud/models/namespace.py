import logging

import jsonschema
import requests

log = logging.getLogger()


class Namespace:
    _responseSchema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "namespace": {
                "type": "object",
                "properties": {
                    "prefix": {"type": "string"},
                    "uri": {"type": "string", "format": "uri"},
                    "isolated": {"type": "boolean"},
                },
                "required": ["prefix", "uri", "isolated"],
            }
        },
        "required": ["namespace"],
    }

    def __init__(self, workspace) -> None:
        self.workspace = workspace
        self.namespace = None

    def put_payload(self, uri=None, isolated="true"):
        payload = {
            "namespace": {"prefix": self.workspace, "uri": uri, "isolated": isolated}
        }
        payload["namespace"] = {
            k: v for k, v in payload["namespace"].items() if v is not None
        }
        return payload

    @property
    def responseSchema(self):
        return self._responseSchema

    def endpoint_url(self):
        return f"/namespaces/{self.workspace}.json"

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
            self.namespace = response.json()
            self.validate(self.settingsWFS)
        else:
            log.error(f"Error: {response.status_code}")
