from typing import Any

from geoservercloud.models.common import EntityModel, ReferencedObjectModel
from geoservercloud.models.styles import Styles


class Layer(EntityModel):
    def __init__(
        self,
        name: str,
        resource_name: str | None = None,
        resource_href: str | None = None,
        type: str | None = None,
        default_style_name: str | None = None,
        styles: list | None = None,
        queryable: bool | None = None,
        attribution: dict[str, int] | None = None,
    ) -> None:
        self.name: str = name
        self.type: str | None = type
        self.resource: ReferencedObjectModel | None = None
        if resource_name:
            self.resource = ReferencedObjectModel(resource_name, resource_href)
        self.default_style: ReferencedObjectModel | None = None
        if default_style_name:
            self.default_style = ReferencedObjectModel(default_style_name)
        self.styles: list | None = styles
        self.queryable: bool | None = queryable
        self.attribution: dict[str, Any] | None = attribution

    @property
    def resource_name(self) -> str | None:
        return self.resource.name if self.resource else None

    @property
    def default_style_name(self) -> str | None:
        return self.default_style.name if self.default_style else None

    @property
    def all_style_names(self) -> set[str]:
        all_styles = set()
        if self.default_style_name is not None:
            all_styles.add(self.default_style_name)
        if self.styles is not None:
            all_styles.update(self.styles)
        return all_styles

    @classmethod
    def from_get_response_payload(cls, content: dict):
        layer = content["layer"]
        if layer.get("styles"):
            styles = Styles.from_get_response_payload(layer).aslist()
        else:
            styles = None
        return cls(
            name=layer["name"],
            resource_name=layer["resource"]["name"],
            resource_href=layer["resource"]["href"],
            type=layer["type"],
            default_style_name=layer["defaultStyle"]["name"],
            styles=styles,
            attribution=layer["attribution"],
            queryable=layer.get("queryable"),
        )

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {"name": self.name}
        if self.styles is not None:
            content.update(Styles(self.styles).post_payload())
        optional_items = {
            "name": self.name,
            "type": self.type,
            "defaultStyle": {
                "name": self.default_style_name,
            },
            "attribution": self.attribution,
            "queryable": self.queryable,
        }
        if self.resource is not None:
            optional_items["resource"] = {
                "name": self.resource.name,
                "href": self.resource.href,
            }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, dict[str, Any]]:
        content = self.asdict()
        if self.resource:
            content["resource"] = self.resource.asdict()
        if self.default_style:
            content["defaultStyle"] = self.default_style.asdict()
        return {"layer": content}

    def put_payload(self) -> dict[str, dict[str, Any]]:
        return self.post_payload()
