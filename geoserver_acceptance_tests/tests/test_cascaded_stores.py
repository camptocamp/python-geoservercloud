import json

from geoservercloud import GeoServerCloud


def test_cascaded_wms(geoserver_factory):
    workspace = "test_cascaded_wms"
    wms_store = "test_cascaded_wms_store"
    wms_url = (
        "https://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
    )
    wms_layer = "ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill"
    geoserver: GeoServerCloud = geoserver_factory(workspace)
    format = "image/jpeg"

    # Create WMS store
    content, status = geoserver.create_wms_store(
        workspace_name=workspace,
        wms_store_name=wms_store,
        capabilities_url=wms_url,
    )
    assert content == wms_store
    assert status == 201

    # Publish layer
    content, status = geoserver.create_wms_layer(
        workspace_name=workspace,
        wms_store_name=wms_store,
        native_layer_name=wms_layer,
    )
    assert content == wms_layer
    assert status == 201

    # Perform GetMap request
    response = geoserver.get_map(
        layers=[wms_layer],
        bbox=(2590000, 1196000, 2605000, 1203000),
        size=(10, 10),
        format=format,
    )
    assert response.info().get("Content-Type") == format

    # Perform GetFeatureInfo request
    response = geoserver.get_feature_info(
        layers=[wms_layer],
        bbox=(2599999.5, 1199999.5, 2600000.5, 1200000.5),
        size=(40, 40),
        info_format="application/json",
        xy=(20, 20),
    )

    # Due to conflicting formats, the forwarding of GetFeatureInfo requests from MapServer
    # through GeoServer is not possible as of 2.28.0
    # See https://sourceforge.net/p/geoserver/mailman/message/30757977/
    data = json.loads(response.read().decode("utf-8"))
    assert data.get("features") == []

    # Delete store
    content, status = geoserver.delete_wms_store(
        workspace_name=workspace, wms_store_name=wms_store
    )
    assert content == ""
    assert status == 200


def test_cascaded_wmts(geoserver_factory):
    workspace = "test_cascaded_wmts"
    wmts_store = "test_cascaded_wmts_store"
    wmts_url = "https://wmts.geo.admin.ch/EPSG/4326/1.0.0/WMTSCapabilities.xml"
    wmts_layer = "ch.swisstopo.pixelkarte-grau"
    geoserver: GeoServerCloud = geoserver_factory(workspace)
    format = "image/jpeg"

    # Create WMTS store
    content, status = geoserver.create_wmts_store(
        workspace_name=workspace,
        name=wmts_store,
        capabilities=wmts_url,
    )
    assert content == wmts_store
    assert status == 201

    # Publish layer (GeoServer)
    content, status = geoserver.create_wmts_layer(
        workspace_name=workspace,
        wmts_store=wmts_store,
        native_layer=wmts_layer,
    )
    assert content == wmts_layer
    assert status == 201

    # Publish the layer in GWC
    content, status = geoserver.publish_gwc_layer(workspace, wmts_layer)
    assert content == ""
    assert status == 200
    content, status = geoserver.get_gwc_layer(workspace, wmts_layer)
    assert status == 200
    assert content.get("GeoServerLayer", {}).get("name") == f"{workspace}:{wmts_layer}"

    # Perform GetTile request (GWC)
    response = geoserver.get_tile(
        layer=f"{workspace}:{wmts_layer}",
        tile_matrix_set="EPSG:4326",
        tile_matrix="EPSG:4326:9",
        row=122,
        column=534,
        format=format,
    )
    assert response.info().get("Content-Type") == format

    # Delete layer and store
    content, code = geoserver.delete_gwc_layer(
        workspace_name=workspace, layer=wmts_layer
    )
    assert content == f"{workspace}:{wmts_layer} deleted"
    assert code == 200

    content, status = geoserver.delete_wmts_store(
        workspace_name=workspace, wmts_store_name=wmts_store
    )
    assert content == ""
    assert status == 200
