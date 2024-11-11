from typing import Any

from geoservercloud.models.common import EntityModel


class Resource(EntityModel):
    def __init__(
        self,
        name: str,
        href: str,
        type: str,
    ) -> None:
        self.name: str = name
        self.href: str = href
        self.type: str = type

    def is_image(self) -> bool:
        return self.type.startswith("image")


class ResourceDirectory(EntityModel):
    def __init__(self, name: str, parent: Resource, children: list[Resource]) -> None:
        self.name: str = name
        self.parent: Resource = parent
        self.children: list[Resource] = children

    @classmethod
    def from_get_response_payload(cls, payload: dict[str, Any]) -> "ResourceDirectory":
        resource_directory = payload["ResourceDirectory"]
        parent = resource_directory["parent"]
        parent = Resource(
            name=parent["path"],
            href=parent["link"]["href"],
            type=parent["link"]["type"],
        )
        children = [
            Resource(child["name"], child["link"]["href"], child["link"]["type"])
            for child in resource_directory.get("children", {}).get("child", [])
        ]
        return cls(
            name=resource_directory["name"],
            parent=parent,
            children=children,
        )
