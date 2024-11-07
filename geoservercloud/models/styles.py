from geoservercloud.models.common import ListModel


class Styles(ListModel):
    def __init__(self, styles: list[str], workspace: str | None = None) -> None:
        self._workspace: str | None = workspace
        self._styles: list[str] = styles

    @property
    def workspace(self) -> str | None:
        return self._workspace

    def aslist(self) -> list[str]:
        return self._styles

    @classmethod
    def from_get_response_payload(cls, content: dict):
        styles: str | dict = content["styles"]
        if not styles:
            return cls([])
        return cls([style["name"] for style in styles["style"]])  # type: ignore

    def post_payload(self) -> dict[str, dict[str, list[dict[str, str]]]]:
        return {"styles": {"style": [{"name": style} for style in self._styles]}}
