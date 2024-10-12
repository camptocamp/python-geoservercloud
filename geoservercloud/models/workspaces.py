import logging

log = logging.getLogger()


class Workspaces:

    def __init__(self, workspaces: dict = {}) -> None:
        self._workspaces = workspaces

    @classmethod
    def validate(self, response):
        try:
            jsonschema.validate(response, self.response_schema)
        except jsonschema.exceptions.ValidationError as err:
            print(err)
            return False
        return True

    def find(self, workspace_name):
        return self.workspaces.get(workspace_name, None)

    @property
    def workspaces(self):
        return self._workspaces

    @classmethod
    def from_response(cls, response):
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
