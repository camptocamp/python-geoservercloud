import json

from geoservercloud.models.common import (
    EntityModel,
    ReferencedObjectModel,
)


class CoverageStore(EntityModel):
    """
    A GeoServer store for coverages (raster layers)
    """

    def __init__(
        self,
        name: str,
        workspace_name: str,
        type: str,
        enabled: bool,
        url: str,
        # Optional fields
        href: str | None = None,
        _default: bool | None = None,
        dateCreated: str | None = None,
        disableOnConnFailure: bool | None = None,
        coverages: str | None = None,
        metadata: dict | None = None,
    ):
        self.name: str = name
        self.workspace: ReferencedObjectModel = ReferencedObjectModel(workspace_name)
        self.type: str = type
        self.enabled: bool = enabled
        self.url: str = url
        self.href: str | None = href
        self._default: bool | None = _default
        self.dateCreated: str | None = dateCreated
        self.disableOnConnFailure: bool | None = disableOnConnFailure
        self.coverages: str | None = coverages
        self.metadata: dict | None = metadata

    @classmethod
    def from_get_response_payload(cls, content: dict):
        store = content["coverageStore"]
        return cls(
            name=store["name"],
            workspace_name=store["workspace"]["name"],
            type=store["type"],
            enabled=store["enabled"],
            url=store["url"],
            href=store.get("href"),
            _default=store.get("_default"),
            dateCreated=store.get("dateCreated"),
            disableOnConnFailure=store.get("disableOnConnFailure"),
            coverages=store.get("coverages"),
        )

    def asdict(self) -> dict[str, object]:
        content = {
            "name": self.name,
            "workspace": self.workspace.name,
            "type": self.type,
            "enabled": self.enabled,
            "url": self.url,
        }
        optional_items = {
            "href": self.href,
            "_default": self._default,
            "dateCreated": self.dateCreated,
            "disableOnConnFailure": self.disableOnConnFailure,
            "coverages": self.coverages,
            "metadata": self.metadata,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, object]:
        content = self.asdict()
        content["workspace"] = {"name": self.workspace.name}
        if self.metadata:
            content["metadata"] = {
                "entry": {"@key": f"{key[0].upper()}{key[1:]}.Key", key: value}
                for key, value in self.metadata.items()
            }
        return {"coverageStore": content}

    def put_payload(self) -> dict[str, object]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return json.dumps(self.post_payload(), indent=4)
