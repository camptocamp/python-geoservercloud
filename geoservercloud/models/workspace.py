import json
from typing import Any

from geoservercloud.models.common import EntityModel


class Workspace(EntityModel):
    def __init__(self, name: str, isolated: bool = False) -> None:
        self.name: str = name
        self.isolated: bool = isolated

    def asdict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "isolated": self.isolated,
        }

    def put_payload(self) -> dict[str, dict[str, Any]]:
        return {"workspace": self.asdict()}

    def post_payload(self) -> dict[str, dict[str, str]]:
        return self.put_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        return cls(
            content["workspace"]["name"],
            content["workspace"]["isolated"],
        )

    def __repr__(self):
        return json.dumps(self.put_payload(), indent=4)
