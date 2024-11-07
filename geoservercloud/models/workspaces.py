from geoservercloud.models.common import ListModel


class Workspaces(ListModel):
    def __init__(self, workspaces: list[dict[str, str]] = []) -> None:
        self._workspaces = workspaces

    def find(self, workspace_name: str) -> dict[str, str] | None:
        for ws in self._workspaces:
            if ws["name"] == workspace_name:
                return ws
        return None

    @classmethod
    def from_get_response_payload(cls, content: dict):

        workspaces: str | dict = content["workspaces"]
        if not workspaces:
            return cls()
        return cls(workspaces["workspace"])  # type: ignore

    def __repr__(self) -> str:
        return str(self._workspaces)

    def aslist(self) -> list[dict[str, str]]:
        return self._workspaces
