from requests.models import Response


class Styles:

    def __init__(self, styles: list[str], workspace: str | None = None) -> None:
        self._workspace = workspace
        self._styles = styles

    @property
    def workspace(self):
        return self._workspace

    @property
    def styles(self):
        return self._styles

    @classmethod
    def from_response(cls, response: Response):
        json_data = response.json()
        styles = []
        try:
            workspace = json_data["styles"]["workspace"]
        except KeyError:
            workspace = None
        try:
            for style in json_data.get("styles", {}).get("style", []):
                styles.append(style["name"])
        except AttributeError:
            styles = []
        return cls(styles, workspace)
