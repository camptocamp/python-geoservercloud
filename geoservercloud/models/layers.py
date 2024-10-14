import logging

import jsonschema
import requests

log = logging.getLogger()


class Layers:

    def __init__(self, workspace_name, layers={}) -> None:
        self.workspace_name = workspace_name
        self.layers = layers

    def endpoint_url(self):
        return f"/workspaces/{self.workspace_name}/layers.json"

    _response_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "layers": {
                "type": "object",
                "properties": {
                    "layer": {
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
                "required": ["layer"],
            }
        },
        "required": ["layers"],
    }

    @property
    def response_schema(self):
        return self._response_schema

    def validate(self, response):
        try:
            log.debug("validate: response = " + str(response))
            if not response["layers"] == "":
                jsonschema.validate(response, self.response_schema)
        except jsonschema.exceptions.ValidationError as err:
            print(err)
            return False
        return True

    def parseResponse(self, response):
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            if not self.validate(json_data):
                raise Exception("Invalid from layers")

            # Map the response to a list of FeatureType instances
            try:
                for feature in json_data.get("layers", {}).get("layer", []):
                    self.layers[feature["name"]] = feature["href"]
            except AttributeError:
                self.layers = {}

            # Now 'layers' is a list of FeatureType instances
            for layer_name, layer_href in self.layers.items():
                log.debug(f"Name: {layer_name}, Href: {layer_href}")
        else:
            log.error(f"Error: {response.status_code}")
