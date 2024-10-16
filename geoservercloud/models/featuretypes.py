import json

from geoservercloud.models import ListModel


class FeatureTypes(ListModel):
    def __init__(self, featuretypes: list = []) -> None:
        self._featuretypes = featuretypes

    @property
    def featuretypes(self):
        return self._featuretypes

    @classmethod
    def from_dict(cls, content: dict):
        featuretypes = []
        for featuretype in content.get("featureTypes", {}).get("featureType", []):
            featuretypes.append(featuretype["name"])
        return cls(featuretypes)

    def __repr__(self):
        return json.dumps(self._featuretypes, indent=4)
