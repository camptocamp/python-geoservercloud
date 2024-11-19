from typing import Any

from geoservercloud.models.common import I18N, EntityModel, ReferencedObjectModel


class LayerGroup(EntityModel):
    modes = ["SINGLE", "OPAQUE_CONTAINER", "NAMED", "CONTAINER", "EO"]

    def __init__(
        self,
        name: str | None = None,
        mode: str | None = None,
        enabled: bool | None = None,
        advertised: bool | None = None,
        workspace_name: str | None = None,
        title: dict[str, str] | str | None = None,
        abstract: dict[str, str] | str | None = None,
        publishables: list[str] | None = None,
        styles: list[str] | None = None,
        bounds: dict[str, Any] | None = None,
    ):
        self.name: str | None = name
        self.mode: str | None = mode
        self.enabled: bool | None = enabled
        self.advertised: bool | None = advertised
        self.workspace: ReferencedObjectModel | None = (
            ReferencedObjectModel(workspace_name) if workspace_name else None
        )
        self.title: I18N | None = (
            I18N(("title", "internationalTitle"), title) if title else None
        )
        self.abstract: I18N | None = (
            I18N(("abstract", "internationalAbstract"), abstract) if abstract else None
        )
        self.publishables: list[ReferencedObjectModel] | None = (
            [ReferencedObjectModel(publishable) for publishable in publishables]
            if publishables
            else None
        )
        self.styles: list[ReferencedObjectModel] | None = (
            [ReferencedObjectModel(style) for style in styles] if styles else None
        )
        self.bounds: dict[str, int | str] | None = bounds

    @property
    def workspace_name(self) -> str | None:
        return self.workspace.name if self.workspace else None

    @classmethod
    def from_get_response_payload(cls, content):
        layer_group: dict[str, Any] = content["layerGroup"]
        # publishables: list of dict or dict (if only one layer)
        publishables: list[dict[str, str]] | dict[str, str] = layer_group[
            "publishables"
        ]["published"]
        if isinstance(publishables, dict):
            publishables = [publishables]
        # style: list of dict, dict (if only one layer) or list of empty strings (if using default layer styles)
        styles: list[dict] | dict | list[str] = layer_group["styles"]["style"]
        if isinstance(styles, dict):
            styles = [styles["name"]]
        if isinstance(styles, list):
            styles = [s["name"] if isinstance(s, dict) else s for s in styles]
        return cls(
            name=layer_group["name"],
            mode=layer_group["mode"],
            enabled=layer_group.get("enabled"),
            advertised=layer_group.get("advertised"),
            workspace_name=layer_group["workspace"]["name"],
            title=layer_group.get("internationalTitle", layer_group.get("title")),
            abstract=layer_group.get(
                "internationalAbstract", layer_group.get("abstract")
            ),
            publishables=[p["name"] for p in publishables],
            styles=styles,
            bounds=layer_group.get("bounds"),
        )

    def asdict(self) -> dict[str, Any]:
        optional_items = {
            "name": self.name,
            "mode": self.mode,
            "enabled": self.enabled,
            "advertised": self.advertised,
            "bounds": self.bounds,
        }
        content = EntityModel.add_items_to_dict({}, optional_items)
        if self.workspace:
            content["workspace"] = self.workspace.asdict()
        if self.publishables:
            content["publishables"] = {
                "published": [
                    {"@type": "layer", "name": p.name} for p in self.publishables
                ]
            }
        if self.styles:
            content["styles"] = {"style": [s.asdict() for s in self.styles]}
        elif self.publishables:
            content["styles"] = {"style": [{"name": ""}] * len(self.publishables)}
        if self.title:
            content.update(self.title.asdict())
        if self.abstract:
            content.update(self.abstract.asdict())
        return content

    def post_payload(self) -> dict[str, Any]:
        return {"layerGroup": self.asdict()}

    def put_payload(self) -> dict[str, Any]:
        content = self.post_payload()
        # Force a null value on non-i18ned attributes, otherwise GeoServer sets it to the first i18n value
        if content["layerGroup"].get("internationalTitle"):
            content["layerGroup"]["title"] = None
        if content["layerGroup"].get("internationalAbstract"):
            content["layerGroup"]["abstract"] = None
        return content
