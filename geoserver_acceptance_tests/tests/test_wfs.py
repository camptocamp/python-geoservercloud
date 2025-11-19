import pytest

from geoservercloud import GeoServerCloud


@pytest.mark.db
def test_wfs(config, geoserver_factory, test_source_directory):
    workspace = datastore = feature_type = "test_wfs"
    geoserver: GeoServerCloud = geoserver_factory(workspace)
    resource_dir = test_source_directory / "resources" / "wfs"
    attributes = {
        "geom": {
            "type": "Point",
            "required": True,
        },
        "id": {
            "type": "integer",
            "required": True,
        },
        "title": {
            "type": "string",
            "required": False,
        },
        "timestamp": {
            "type": "datetime",
            "required": False,
        },
    }
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
    # Create GeoServer feature type - this also creates the DB table
    content, code = geoserver.create_feature_type(
        feature_type, attributes=attributes, epsg=2056, workspace_name=workspace
    )
    assert content == ""
    assert code == 201

    # Post a feature through a WFS request
    with open(str(resource_dir / "wfs_insert_payload.xml")) as file:
        data = file.read()
        response = geoserver.rest_service.rest_client.post(
            f"/{workspace}/wfs/", data=data
        )
        assert response.status_code == 200

    # GetFeature request
    feature_collection = geoserver.get_feature(workspace, feature_type)
    assert type(feature_collection) is dict
    features = feature_collection.get("features")
    assert type(features) is list
    assert len(features) == 1, f"Expected exactly 1 feature, got {len(features)}"
    feature = features[0]
    properties = feature.get("properties")
    assert properties.get("id") == 10
    assert properties.get("title") == "Title"
    assert properties.get("timestamp") == "2024-05-13T08:14:48.763Z"
    assert feature.get("geometry", {}) == {
        "type": "Point",
        "coordinates": [2600000, 1200000],
    }
    assert feature_collection.get("crs") == {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:EPSG::2056"},
    }

    # Delete feature through WFS request
    with open(str(resource_dir / "wfs_delete_payload.xml")) as file:
        data = file.read()
        response = geoserver.rest_service.rest_client.post(
            f"/{workspace}/wfs/", data=data
        )
        assert response.status_code == 200
    feature_collection = geoserver.get_feature(workspace, feature_type)
    assert type(feature_collection) is dict
    features = feature_collection.get("features")
    assert type(features) is list
    assert len(features) == 0, f"Expected 0 features, got {len(features)}"
