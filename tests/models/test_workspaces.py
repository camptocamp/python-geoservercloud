from geoservercloud.models import Workspaces


def test_workspaces_initialization():
    initial_workspaces = {"Workspace1": "http://example.com/ws1"}
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.workspaces == initial_workspaces


def test_workspaces_find_existing():
    initial_workspaces = {"Workspace1": "http://example.com/ws1"}
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.find("Workspace1") == "http://example.com/ws1"


def test_workspaces_find_non_existing():
    workspaces = Workspaces({"Workspace1": "http://example.com/ws1"})

    assert workspaces.find("NonExistingWorkspace") is None


def test_workspaces_from_dict_empty():
    mock_response = {"workspaces": {}}

    workspaces = Workspaces.from_dict(mock_response)

    assert workspaces.workspaces == []
