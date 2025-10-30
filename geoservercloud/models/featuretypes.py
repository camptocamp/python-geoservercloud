from geoservercloud.models.common import ListModel


class FeatureTypes(ListModel[dict[str, str]]):
    _list_key = "featureTypes"
    _item_key = "featureType"
