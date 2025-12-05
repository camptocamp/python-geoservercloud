import json
from pathlib import Path

import pytest
from sqlalchemy.sql import text

from geoservercloud import GeoServerCloud
from geoservercloud.templates import Templates

from .utils import compare_images, write_actual_image


@pytest.mark.db
def test_create_feature_type_and_get_map(
    db_session,
    config,
    geoserver_factory,
    test_source_directory,
    tmp_path_persistent,
):
    workspace = datastore = feature_type = "test_create_feature_type"
    geoserver: GeoServerCloud = geoserver_factory(workspace)
    resource_dir = test_source_directory / "resources" / "wms"
    geoserver.create_pg_datastore(
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
    _, status = geoserver.create_feature_type(
        feature_type,
        attributes=Templates.geom_point_attribute(),
        epsg=2056,
        workspace_name=workspace,
    )
    assert status == 201

    # Create feature
    table = f"{config['db']['pg_schema']}.{feature_type}"
    db_session.execute(
        text(
            f"INSERT INTO {table} (geom) VALUES (public.ST_SetSRID(public.ST_MakePoint(2600000, 1200000), 2056))"
        )
    )
    db_session.commit()

    # GetMap request
    response = geoserver.get_map(
        layers=[feature_type],
        bbox=(2599999.5, 1199999.5, 2600000.5, 1200000.5),
        size=(40, 40),
        format="image/png",
        transparent=False,
    )

    file_root = Path("getmap")
    write_actual_image(tmp_path_persistent, file_root, response)
    compare_images(tmp_path_persistent, resource_dir, file_root)


@pytest.mark.db
def test_get_feature_info(db_session, config, geoserver_factory):
    workspace = datastore = feature_type = "test_get_feature_info"
    geoserver: GeoServerCloud = geoserver_factory(workspace)
    attributes = {
        "geom": {
            "type": "Point",
            "required": True,
        },
        "label": {
            "type": "string",
            "required": False,
        },
    }
    _, status = geoserver.create_pg_datastore(
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
    assert status == 201
    _, status = geoserver.create_feature_type(
        feature_type, attributes=attributes, epsg=2056, workspace_name=workspace
    )
    assert status == 201

    # Create feature
    table = f"{config['db']['pg_schema']}.{feature_type}"
    db_session.execute(
        text(
            f"INSERT INTO {table} (geom, label) VALUES "
            "(public.ST_SetSRID(public.ST_MakePoint(2600000, 1200000), 2056), 'Label')"
        )
    )
    db_session.commit()

    # Test that layer is published
    _, status = geoserver.get_feature_type(workspace, datastore, feature_type)
    assert status == 200

    # GetFeatureInfo request
    response = geoserver.get_feature_info(
        layers=[feature_type],
        bbox=(2599999.5, 1199999.5, 2600000.5, 1200000.5),
        size=(40, 40),
        info_format="application/json",
        xy=[20, 20],
        workspace_name=workspace,
    )

    data = json.loads(response.read().decode("utf-8"))

    feature = data.get("features", [])[0]
    assert feature
    assert feature.get("properties").get("label") == "Label"
    assert feature.get("geometry") == {
        "type": "Point",
        "coordinates": [2600000, 1200000],
    }
    assert data.get("crs") == {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:EPSG::2056"},
    }
