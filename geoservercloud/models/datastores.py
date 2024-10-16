from geoservercloud.models import ListModel


class DataStores(ListModel):
    def __init__(self, datastores: list[dict[str, str]] = []) -> None:
        self._datastores: list[dict[str, str]] = datastores

    @classmethod
    def from_get_response_payload(cls, content: dict):
        datastores: str | dict = content["dataStores"]
        if not datastores:
            return cls()
        return cls(datastores["dataStore"])  # type: ignore

    def __repr__(self) -> str:
        return str(self._datastores)

    def aslist(self) -> list[dict[str, str]]:
        return self._datastores
