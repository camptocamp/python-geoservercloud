from geoservercloud.models.common import ListModel


class Styles(ListModel[dict[str, str]]):
    _list_key = "styles"
    _item_key = "style"

    def __init__(
        self, styles: list[dict[str, str]] | None = None, workspace: str | None = None
    ) -> None:
        super().__init__(styles)
        self._workspace: str | None = workspace

    @property
    def workspace(self) -> str | None:
        return self._workspace

    def post_payload(self) -> dict[str, dict[str, list[dict[str, str]]]]:
        # Convert items to the expected format for POST requests
        items = []
        for item in self._items:
            if isinstance(item, dict):
                items.append({"name": item["name"]})
            else:
                items.append({"name": item})
        return {"styles": {"style": items}}
