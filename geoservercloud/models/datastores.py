from geoservercloud.models.common import ListModel


class DataStores(ListModel):
    def __init__(self, datastores: list[str] = []) -> None:
        self._datastores: list[str] = datastores

    @classmethod
    def from_get_response_payload(cls, content: dict):
        datastores: dict | str = content["dataStores"]
        if not datastores:
            return cls()
        return cls([ds["name"] for ds in datastores["dataStore"]])  # type: ignore

    def __repr__(self) -> str:
        return str([{"name": ds} for ds in self._datastores])

    def aslist(self) -> list[str]:
        return self._datastores
