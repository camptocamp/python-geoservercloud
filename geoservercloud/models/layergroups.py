import json

from geoservercloud.models.common import ListModel


class LayerGroups(ListModel):
    def __init__(self, layergroups: list = []) -> None:
        self._layergroups = layergroups

    @classmethod
    def from_get_response_payload(cls, content: dict):
        feature_types: str | dict = content["layerGroups"]
        if not feature_types:
            return cls()
        return cls(feature_types["layerGroup"])  # type: ignore

    def aslist(self) -> list[dict[str, str]]:
        return self._layergroups

    def __repr__(self):
        return json.dumps(self._layergroups, indent=4)
