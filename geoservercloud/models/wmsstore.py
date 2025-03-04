import json
from typing import Any

from geoservercloud.models.common import (
    EntityModel,
    KeyDollarListDict,
    ReferencedObjectModel,
)


class WmsStore(EntityModel):
    def __init__(
        self,
        workspace_name: str,
        name: str,
        capabilities_url: str,
        type: str = "WMS",
        enabled: bool = True,
        default: bool | None = None,
        disable_on_conn_failure: bool | None = None,
    ) -> None:
        self.workspace: ReferencedObjectModel = ReferencedObjectModel(workspace_name)
        self._name: str = name
        self.capabilities_url: str = capabilities_url
        self.type: str = type
        self.enabled: bool = enabled
        self._default: bool | None = default
        self.disable_on_conn_failure: bool | None = disable_on_conn_failure

    @property
    def name(self) -> str:
        return self._name

    @property
    def workspace_name(self) -> str:
        return self.workspace.name

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {
            "name": self._name,
            "type": self.type,
            "workspace": self.workspace_name,
            "capabilitiesURL": self.capabilities_url,
        }
        optional_items = {
            "enabled": self.enabled,
            "_default": self._default,
            "disableOnConnFailure": self.disable_on_conn_failure,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        content = self.asdict()
        content["workspace"] = {"name": self.workspace_name}
        return {"wmsStore": content}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        wms_store = content["wmsStore"]
        return cls(
            wms_store["workspace"]["name"],
            wms_store["name"],
            wms_store["capabilitiesURL"],
            wms_store.get("type", "PostGIS"),
            wms_store.get("enabled", True),
            wms_store.get("_default", None),
            wms_store.get("disableOnConnFailure", None),
        )

    def __repr__(self) -> str:
        return json.dumps(self.put_payload(), indent=4)
