from pytest import fixture

from geoservercloud.models.workspaces import Workspaces


@fixture(scope="module")
def initial_workspaces():
    return [
        {
            "name": "Workspace1",
            "href": "http://example.com/ws1",
        }
    ]


def test_workspaces_initialization(initial_workspaces):
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.aslist() == initial_workspaces


def test_workspaces_find_existing(initial_workspaces):
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.find("Workspace1") == initial_workspaces[0]


def test_workspaces_find_non_existing(initial_workspaces):
    workspaces = Workspaces(initial_workspaces)

    assert workspaces.find("NonExistingWorkspace") is None


def test_workspaces_from_get_response_payload_empty():
    mock_response = {"workspaces": ""}

    workspaces = Workspaces.from_get_response_payload(mock_response)

    assert workspaces.aslist() == []
