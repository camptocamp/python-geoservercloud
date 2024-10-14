import logging

from requests.models import Response

log = logging.getLogger()


class Workspaces:

    def __init__(self, workspaces: list = []) -> None:
        self._workspaces = workspaces

    def find(self, workspace_name: str):
        return self.workspaces.get(workspace_name, None)

    @property
    def workspaces(self):
        return self._workspaces

    @classmethod
    def from_response(cls, response: Response):
        # Parse the JSON response
        json_data = response.json()

        workspaces = []
        # Map the response to a list of Workspace instances
        for ws in json_data.get("workspaces", {}).get("workspace", []):
            workspaces.append(ws["name"])

        # Now 'workspaces' is a list of Workspace instances
        log.debug("Parsed Workspaces:")
        for workspace in workspaces:
            log.debug(f"Name: {workspace}")

        return cls(workspaces)
