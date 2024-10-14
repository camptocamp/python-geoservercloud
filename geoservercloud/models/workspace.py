import json
import logging

from requests.models import Response

log = logging.getLogger()


class Workspace:

    def __init__(self, name: str, isolated: bool = False) -> None:
        self.name = name
        self.isolated = isolated

    def put_payload(self):
        payload = {"workspace": {"name": self.name}}
        if self.isolated:
            payload["workspace"]["isolated"] = self.isolated
        return payload

    def post_payload(self):
        return self.put_payload()

    @classmethod
    def from_response(cls, response: Response):
        json_data = response.json()
        return cls(
            json_data.get("workspace", {}).get("name", None),
            json_data.get("workspace", {}).get("isolated", False),
        )
        return cls(json_data.get("workspace", {}).get("name", None))

    def __repr__(self):
        return json.dumps(self.put_payload(), indent=4)
