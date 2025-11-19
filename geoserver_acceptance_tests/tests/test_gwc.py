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

    content, status = geoserver.publish_gwc_layer(workspace, wmts_layer)
    assert status == 200
    assert content == ""

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
