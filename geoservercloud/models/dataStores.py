import logging

import jsonschema
import requests

log = logging.getLogger()


class DataStores:

    def __init__(self, workspace_name: str, datastores: list[str] = []) -> None:
        self.workspace_name = workspace_name
        self._datastores = datastores

    @property
    def datastores(self):
        return self._datastores

    @classmethod
    def from_response(cls, response):
        json_data = response.json()
        datastores = []
        workspace_name = (
            json_data.get("dataStores", {}).get("workspace", {}).get("name", None)
        )
        for store in json_data.get("dataStores", {}).get("dataStore", []):
            datastores.append(store["name"])
            for data_store_name in datastores:
                log.debug(f"Name: {data_store_name}")
        return cls(workspace_name, datastores)

    def __repr__(self):
        return str(self.datastores)