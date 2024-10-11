import logging

from . import KeyDollarListDict

log = logging.getLogger()


class PostGisDataStore:

    def __init__(
        self,
        workspace_name: str,
        data_store_name: str,
        connection_parameters: KeyDollarListDict,
        data_store_type: str = "PostGIS",
        enabled: bool = True,
        description: str | None = None,
    ) -> None:
        self.workspace_name = workspace_name
        self.data_store_name = data_store_name
        self.connection_parameters = connection_parameters
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
    def from_response(cls, response):

        json_data = response.json()
        connection_parameters = cls.parse_connection_parameters(json_data)
        return cls(
            json_data.get("dataStore", {}).get("workspace", {}).get("name", None),
            json_data.get("dataStore", {}).get("name", None),
            connection_parameters,
            json_data.get("dataStore", {}).get("type", "PostGIS"),
            json_data.get("dataStore", {}).get("enabled", True),
            json_data.get("dataStore", {}).get("description", None),
        )

    @classmethod
    def parse_connection_parameters(cls, json_data):
        return KeyDollarListDict(
            json_data.get("dataStore", {})
            .get("connectionParameters", {})
            .get("entry", [])
        )
