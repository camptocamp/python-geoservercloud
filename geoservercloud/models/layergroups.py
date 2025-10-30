from geoservercloud.models.common import ListModel


class LayerGroups(ListModel[dict[str, str]]):
    _list_key = "layerGroups"
    _item_key = "layerGroup"
