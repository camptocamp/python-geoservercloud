from geoservercloud.models.common import ListModel


class Workspaces(ListModel[dict[str, str]]):
    _list_key = "workspaces"
    _item_key = "workspace"
