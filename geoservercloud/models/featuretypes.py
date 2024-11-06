import json

from geoservercloud.models import ListModel


class FeatureTypes(ListModel):
    def __init__(self, featuretypes: list = []) -> None:
        self._featuretypes: list[str] = featuretypes

    @classmethod
    def from_get_response_payload(cls, content: dict):
        feature_types: str | dict = content["featureTypes"]
        if not feature_types:
            return cls([])
        return cls([feature_type["name"] for feature_type in feature_types["featureType"]])  # type: ignore

    def aslist(self) -> list[str]:
        return self._featuretypes

    def __repr__(self):
        return json.dumps(self._featuretypes, indent=4)
