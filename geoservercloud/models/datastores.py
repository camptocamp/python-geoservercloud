from geoservercloud.models.common import ListModel


class DataStores(ListModel[dict[str, str]]):
    _list_key = "dataStores"
    _item_key = "dataStore"
