import logging

import jsonschema
import requests

log = logging.getLogger()


class LayerGroups:

    def __init__(self, workspace_name, layerGroups={}) -> None:
        self.workspace_name = workspace_name
        self.layerGroups = layerGroups

    def endpoint_url(self):
        return f"/workspaces/{self.workspace_name}/layergroups.json"

    _response_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "layerGroups": {
                "type": "object",
                "properties": {
                    "layerGroup": {
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
                "required": ["layerGroup"],
            }
        },
        "required": ["layerGroups"],
    }

    @property
    def response_schema(self):
        return self._response_schema

    def validate(self, response):
        try:
            log.debug("validate: response = " + str(response))
            if not response["layerGroups"] == "":
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
                raise Exception("Invalid from layerGroups")

            # Map the response to a list of FeatureType instances
            try:
                for layergroup in json_data.get("layerGroups", {}).get(
                    "layerGroup", []
                ):
                    self.layerGroups[layergroup["name"]] = layergroup["href"]
            except AttributeError:
                self.layerGroups = {}

            # Now 'layerGroups' is a list of FeatureType instances
            for layergroup_type_name, layergroup_type_href in self.layerGroups.items():
                log.debug(f"Name: {layergroup_type_name}, Href: {layergroup_type_href}")
        else:
            log.error(f"Error: {response.status_code}")
