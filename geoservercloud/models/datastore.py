import json
import logging

from requests.models import Response

from . import KeyDollarListDict

log = logging.getLogger()


class PostGisDataStore:

    def __init__(
        self,
        workspace_name: str,
        data_store_name: str,
        connection_parameters: dict,
        data_store_type: str = "PostGIS",
        enabled: bool = True,
        description: str | None = None,
    ) -> None:
        self.workspace_name = workspace_name
        self.data_store_name = data_store_name
        self.connection_parameters = KeyDollarListDict(input_dict=connection_parameters)
        self.data_store_type = data_store_type
        self.description = description
        self.enabled = enabled

    @property
    def name(self):
        return self.data_store_name

    def post_payload(self):
        payload = {
            "dataStore": {
                "name": self.data_store_name,
                "type": self.data_store_type,
                "connectionParameters": {
                    "entry": self.connection_parameters.serialize()
                },
            }
        }
        if self.description:
            payload["dataStore"]["description"] = self.description
        if self.enabled:
            payload["dataStore"]["enabled"] = self.enabled
        return payload

    def put_payload(self):
        payload = self.post_payload()
        return payload

    @classmethod
    def from_dict(cls, content: dict):
        connection_parameters = cls.parse_connection_parameters(content)
        return cls(
            content.get("dataStore", {}).get("workspace", {}).get("name", None),
            content.get("dataStore", {}).get("name", None),
            connection_parameters,
            content.get("dataStore", {}).get("type", "PostGIS"),
            content.get("dataStore", {}).get("enabled", True),
            content.get("dataStore", {}).get("description", None),
        )

    @classmethod
    def parse_connection_parameters(cls, content):
        return KeyDollarListDict(
            content.get("dataStore", {})
            .get("connectionParameters", {})
            .get("entry", [])
        )

    def __repr__(self):
        return json.dumps(self.put_payload(), indent=4)
