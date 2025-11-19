from geoservercloud import GeoServerCloud


def test_crud_workspace(geoserver: GeoServerCloud):

    workspaces, status = geoserver.get_workspaces()
    assert status == 200
    assert type(workspaces) is list

    workspace_name = "acceptance_test_workspace"

    content, status = geoserver.create_workspace(workspace_name)
    assert status == 201
    assert content == workspace_name

    workspace, status = geoserver.get_workspace(workspace_name)
    assert status == 200
    assert type(workspace) is dict
    assert workspace == {"name": workspace_name, "isolated": False}

    content, status = geoserver.delete_workspace(workspace_name)
    assert status == 200
    assert content == ""
