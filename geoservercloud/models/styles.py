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
    def from_dict(cls, content: dict):
        styles = []
        try:
            workspace = content["styles"]["workspace"]
        except KeyError:
            workspace = None
        try:
            for style in content.get("styles", {}).get("style", []):
                styles.append(style["name"])
        except AttributeError:
            styles = []
        return cls(styles, workspace)
