import logging

from requests.models import Response

log = logging.getLogger()


class DataStores:

    def __init__(self, workspace_name: str, datastores: list[str] = []) -> None:
        self.workspace_name = workspace_name
        self._datastores = datastores

    @property
    def datastores(self):
        return self._datastores

    @classmethod
    def from_dict(cls, content: dict):
        datastores = []
        workspace_name = (
            content.get("dataStores", {}).get("workspace", {}).get("name", None)
        )

        for store in content.get("dataStores", {}).get("dataStore", []):
            datastores.append(store["name"])
            for data_store_name in datastores:
                log.debug(f"Name: {data_store_name}")
        return cls(workspace_name, datastores)

    def __repr__(self):
        return str(self.datastores)
