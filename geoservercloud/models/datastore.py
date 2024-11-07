import json
from typing import Any

from geoservercloud.models.common import (
    EntityModel,
    KeyDollarListDict,
    ReferencedObjectModel,
)


class PostGisDataStore(EntityModel):
    def __init__(
        self,
        workspace_name: str,
        name: str,
        connection_parameters: dict,
        type: str = "PostGIS",
        enabled: bool = True,
        description: str | None = None,
        default: bool | None = None,
        disable_on_conn_failure: bool | None = None,
    ) -> None:
        self.workspace: ReferencedObjectModel = ReferencedObjectModel(workspace_name)
        self._name: str = name
        self.connection_parameters = KeyDollarListDict(input_dict=connection_parameters)
        self.type: str = type
        self.description: str | None = description
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
            "connectionParameters": {"entry": dict(self.connection_parameters)},
            "workspace": self.workspace_name,
        }
        optional_items = {
            "description": self.description,
            "enabled": self.enabled,
            "_default": self._default,
            "disableOnConnFailure": self.disable_on_conn_failure,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        content = self.asdict()
        content["connectionParameters"] = {
            "entry": self.connection_parameters.serialize()
        }
        content["workspace"] = {"name": self.workspace_name}
        return {"dataStore": content}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        data_store = content["dataStore"]
        connection_parameters = KeyDollarListDict(
            input_list=data_store["connectionParameters"]["entry"]
        )
        return cls(
            data_store["workspace"]["name"],
            data_store["name"],
            connection_parameters,
            data_store.get("type", "PostGIS"),
            data_store.get("enabled", True),
            data_store.get("description", None),
            data_store.get("_default", None),
            data_store.get("disableOnConnFailure", None),
        )

    def __repr__(self) -> str:
        return json.dumps(self.put_payload(), indent=4)
