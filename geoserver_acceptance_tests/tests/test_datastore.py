import pytest

from geoservercloud import GeoServerCloud


@pytest.mark.db
def test_create_get_and_delete_datastore(config, geoserver_factory):
    workspace = "test_pg_datastore"
    datastore = "test_pg_datastore"
    geoserver: GeoServerCloud = geoserver_factory(workspace)
    content, code = geoserver.create_pg_datastore(
        workspace_name=workspace,
        datastore_name=datastore,
        pg_host=config["db"]["pg_host"]["docker"],
        pg_port=config["db"]["pg_port"]["docker"],
        pg_db=config["db"]["pg_db"],
        pg_user=config["db"]["pg_user"],
        pg_password=config["db"]["pg_password"],
        pg_schema=config["db"]["pg_schema"],
        set_default_datastore=True,
    )
    assert content == datastore
    assert code == 201
    content, code = geoserver.get_pg_datastore(workspace, datastore)
    assert content.get("name") == datastore
    assert code == 200
