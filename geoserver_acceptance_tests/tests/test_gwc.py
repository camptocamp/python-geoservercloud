import time

import pytest

from geoservercloud import GeoServerCloud


def test_tile_cache(geoserver_factory):
    workspace = "test_gwc"
    wmts_store = "test_gwc_store"
    wmts_layer = "ch.swisstopo.swissimage"
    geoserver: GeoServerCloud = geoserver_factory(workspace)

    content, status = geoserver.create_wmts_store(
        workspace,
        wmts_store,
        capabilities="https://wmts.geo.admin.ch/EPSG/4326/1.0.0/WMTSCapabilities.xml",
    )
    assert status == 201
    assert content == wmts_store

    content, status = geoserver.create_wmts_layer(workspace, wmts_store, wmts_layer)
    assert status == 201
    assert content == wmts_layer

    # with automatic tile caching enabled the tile layer is created with the
    # WMTS layer; wait for it before publishing over it, GeoServer Cloud
    # propagates the new layer between services asynchronously
    assert wait_for_tile_layer_status(geoserver, workspace, wmts_layer, 200) == 200

    content, status = geoserver.publish_gwc_layer(workspace, wmts_layer)
    assert status == 200
    assert content in ["", "layer saved"]

    response = geoserver.get_tile(
        format="image/png",
        layer=f"{workspace}:{wmts_layer}",
        tile_matrix_set="EPSG:4326",
        tile_matrix="EPSG:4326:9",
        row=122,
        column=534,
    )
    assert response.info().get("Content-Type") == "image/png"
    assert response.info().get("Geowebcache-Cache-Result") == "MISS"

    response = geoserver.get_tile(
        format="image/png",
        layer=f"{workspace}:{wmts_layer}",
        tile_matrix_set="EPSG:4326",
        tile_matrix="EPSG:4326:9",
        row=122,
        column=534,
    )
    assert response.info().get("Geowebcache-Cache-Result") == "HIT"


def wait_for_tile_layer_status(
    geoserver, workspace, layer, expected_status, timeout=30
):
    """Poll the GWC REST API until the tile layer reaches the expected status.

    GeoServer Cloud propagates catalog changes between services asynchronously;
    against a monolithic GeoServer the first poll already settles.
    """
    deadline = time.monotonic() + timeout
    status = None
    while time.monotonic() < deadline:
        _, status = geoserver.get_gwc_layer(workspace, layer)
        if status == expected_status:
            return status
        time.sleep(0.5)
    return status


@pytest.mark.db
def test_automatic_tile_layer_lifecycle(config, geoserver_factory):
    """Tile layers must follow REST catalog changes when automatic caching is on.

    Regression test for https://github.com/geoserver/geoserver-cloud/issues/519
    """
    workspace = datastore = "test_gwc_auto"
    feature_type = "auto_cached_layer"
    renamed = "auto_cached_layer_renamed"
    geoserver: GeoServerCloud = geoserver_factory(workspace)

    _, code = geoserver.create_pg_datastore(
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
    assert code == 201

    attributes = {
        "geom": {"type": "Point", "required": True},
        "id": {"type": "integer", "required": True},
    }
    _, code = geoserver.create_feature_type(
        feature_type, attributes=attributes, epsg=4326, workspace_name=workspace
    )
    assert code == 201

    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 200) == 200

    response = geoserver.rest_service.rest_client.put(
        f"/rest/workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_type}.json",
        json={"featureType": {"name": renamed}},
    )
    assert response.status_code == 200

    assert wait_for_tile_layer_status(geoserver, workspace, renamed, 200) == 200
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 404) == 404

    _, code = geoserver.delete_feature_type(workspace, datastore, renamed)
    assert code == 200

    assert wait_for_tile_layer_status(geoserver, workspace, renamed, 404) == 404


@pytest.mark.db
def test_tile_layer_follows_workspace_rename(config, geoserver_factory):
    """Renaming a workspace must rename all its tile layers (prefixed names).

    Regression test for https://github.com/geoserver/geoserver-cloud/issues/519
    """
    workspace = datastore = "test_gwc_wsrename"
    renamed_workspace = "test_gwc_wsrenamed"
    feature_type = "ws_rename_layer"
    geoserver: GeoServerCloud = geoserver_factory(workspace)

    _, code = geoserver.create_pg_datastore(
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
    assert code == 201

    attributes = {"geom": {"type": "Point", "required": True}}
    _, code = geoserver.create_feature_type(
        feature_type, attributes=attributes, epsg=4326, workspace_name=workspace
    )
    assert code == 201
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 200) == 200

    response = geoserver.rest_service.rest_client.put(
        f"/rest/workspaces/{workspace}.json",
        json={"workspace": {"name": renamed_workspace}},
    )
    assert response.status_code == 200

    try:
        assert (
            wait_for_tile_layer_status(geoserver, renamed_workspace, feature_type, 200)
            == 200
        )
        assert (
            wait_for_tile_layer_status(geoserver, workspace, feature_type, 404) == 404
        )
    finally:
        # rename back to the original name for the workspace cleanup finalizer
        geoserver.rest_service.rest_client.put(
            f"/rest/workspaces/{renamed_workspace}.json",
            json={"workspace": {"name": workspace}},
        )


@pytest.mark.db
def test_tile_layer_rename_after_tile_layer_recreated_through_gwc(
    config, geoserver_factory
):
    """Layer renames must reach every service even when the service handling the
    rename has not touched the tile layer since another service last changed it.

    The tile layer is deleted and recreated through the GWC service, then the
    feature type is renamed through the REST API. The tile layer must follow the
    rename regardless of which service changed it last.
    """
    workspace = datastore = "test_gwc_coldrename"
    feature_type = "cold_rename_layer"
    renamed = "cold_rename_layer_renamed"
    geoserver: GeoServerCloud = geoserver_factory(workspace)

    _, code = geoserver.create_pg_datastore(
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
    assert code == 201

    attributes = {"geom": {"type": "Point", "required": True}}
    _, code = geoserver.create_feature_type(
        feature_type, attributes=attributes, epsg=4326, workspace_name=workspace
    )
    assert code == 201
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 200) == 200

    # recreate the tile layer through the GWC service
    _, code = geoserver.delete_gwc_layer(workspace, feature_type)
    assert code == 200
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 404) == 404
    _, code = geoserver.publish_gwc_layer(workspace, feature_type)
    assert code == 200
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 200) == 200

    # rename the feature type through the REST API
    response = geoserver.rest_service.rest_client.put(
        f"/rest/workspaces/{workspace}/datastores/{datastore}/featuretypes/{feature_type}.json",
        json={"featureType": {"name": renamed}},
    )
    assert response.status_code == 200

    assert wait_for_tile_layer_status(geoserver, workspace, renamed, 200) == 200
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 404) == 404

    _, code = geoserver.delete_feature_type(workspace, datastore, renamed)
    assert code == 200


@pytest.mark.db
def test_workspace_rename_after_tile_layer_recreated_through_gwc(
    config, geoserver_factory
):
    """Workspace renames must rename tile layers even when the service handling
    the rename has not touched them since another service last changed them.
    """
    workspace = datastore = "test_gwc_coldws"
    renamed_workspace = "test_gwc_coldws_renamed"
    feature_type = "cold_ws_layer"
    geoserver: GeoServerCloud = geoserver_factory(workspace)

    _, code = geoserver.create_pg_datastore(
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
    assert code == 201

    attributes = {"geom": {"type": "Point", "required": True}}
    _, code = geoserver.create_feature_type(
        feature_type, attributes=attributes, epsg=4326, workspace_name=workspace
    )
    assert code == 201
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 200) == 200

    # recreate the tile layer through the GWC service
    _, code = geoserver.delete_gwc_layer(workspace, feature_type)
    assert code == 200
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 404) == 404
    _, code = geoserver.publish_gwc_layer(workspace, feature_type)
    assert code == 200
    assert wait_for_tile_layer_status(geoserver, workspace, feature_type, 200) == 200

    # rename the workspace through the REST API
    response = geoserver.rest_service.rest_client.put(
        f"/rest/workspaces/{workspace}.json",
        json={"workspace": {"name": renamed_workspace}},
    )
    assert response.status_code == 200

    try:
        assert (
            wait_for_tile_layer_status(geoserver, renamed_workspace, feature_type, 200)
            == 200
        )
        assert (
            wait_for_tile_layer_status(geoserver, workspace, feature_type, 404) == 404
        )
    finally:
        geoserver.rest_service.rest_client.put(
            f"/rest/workspaces/{renamed_workspace}.json",
            json={"workspace": {"name": workspace}},
        )
