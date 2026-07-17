import json
from typing import Any

from geoservercloud.models.common import (
    EntityModel,
    KeyDollarListDict,
    ReferencedObjectModel,
)


class WmtsStore(EntityModel):
    def __init__(
        self,
        workspace_name: str,
        name: str,
        capabilities_url: str,
        type: str = "WMTS",
        enabled: bool = True,
        default: bool | None = None,
        disable_on_conn_failure: bool | None = None,
        use_connection_pooling: bool | None = None,
        max_connections: int | None = None,
        read_timeout: int | None = None,
        connect_timeout: int | None = None,
        date_created: str | None = None,
        date_modified: str | None = None,
    ) -> None:
        self.workspace: ReferencedObjectModel = ReferencedObjectModel(workspace_name)
        self._name: str = name
        self.capabilities_url: str = capabilities_url
        self.type: str = type
        self.enabled: bool = enabled
        self._default: bool | None = default
        self.disable_on_conn_failure: bool | None = disable_on_conn_failure
        self.metadata: KeyDollarListDict | None = None
        if use_connection_pooling is not None:
            self.metadata = KeyDollarListDict(
                input_dict={"useConnectionPooling": str(use_connection_pooling).lower()}
            )
        self.max_connections: int | None = max_connections
        self.read_timeout: int | None = read_timeout
        self.connect_timeout: int | None = connect_timeout
        self.date_created: str | None = date_created
        self.date_modified: str | None = date_modified

    @property
    def name(self) -> str:
        return self._name

    @property
    def workspace_name(self) -> str:
        return self.workspace.name

    @property
    def use_connection_pooling(self) -> bool | None:
        if self.metadata is None:
            return None
        value = self.metadata.get("useConnectionPooling")
        return None if value is None else value == "true"

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {
            "name": self._name,
            "type": self.type,
            "workspace": self.workspace_name,
            "capabilitiesURL": self.capabilities_url,
        }
        optional_items: dict[str, Any] = {
            "enabled": self.enabled,
            "_default": self._default,
            "disableOnConnFailure": self.disable_on_conn_failure,
            "maxConnections": self.max_connections,
            "readTimeout": self.read_timeout,
            "connectTimeout": self.connect_timeout,
            "dateCreated": self.date_created,
            "dateModified": self.date_modified,
        }
        if self.metadata:
            optional_items["metadata"] = {"entry": dict(self.metadata)}
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        content = self.asdict()
        content["workspace"] = {"name": self.workspace_name}
        if self.metadata:
            content["metadata"] = {"entry": self.metadata.serialize()}
        return {"wmtsStore": content}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        wmts_store = content["wmtsStore"]
        use_connection_pooling: bool | None = None
        metadata_entry = wmts_store.get("metadata", {}).get("entry")
        if isinstance(metadata_entry, dict):
            metadata_entry = [metadata_entry]
        if metadata_entry:
            metadata = KeyDollarListDict(input_list=metadata_entry)
            value = metadata.get("useConnectionPooling")
            if value is not None:
                use_connection_pooling = str(value).lower() == "true"
        return cls(
            wmts_store["workspace"]["name"],
            wmts_store["name"],
            wmts_store["capabilitiesURL"],
            wmts_store.get("type", "WMTS"),
            wmts_store.get("enabled", True),
            wmts_store.get("_default", None),
            wmts_store.get("disableOnConnFailure", None),
            use_connection_pooling,
            wmts_store.get("maxConnections", None),
            wmts_store.get("readTimeout", None),
            wmts_store.get("connectTimeout", None),
            wmts_store.get("dateCreated", None),
            wmts_store.get("dateModified", None),
        )

    def __repr__(self) -> str:
        return json.dumps(self.put_payload(), indent=4)
