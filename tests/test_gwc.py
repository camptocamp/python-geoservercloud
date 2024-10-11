import responses

from geoservercloud import GeoServerCloud

WORKSPACE = "test_workspace"
LAYER = "test_layer"
EPSG = 3857
CAPABILITIES = """<?xml version="1.0" encoding="UTF-8"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" version="1.0.0" xmlns:ows="http://www.opengis.net/ows/1.1">
    <Contents>
        <Layer>
            <ows:Identifier>test_layer</ows:Identifier>
            <ows:WGS84BoundingBox>
                <ows:LowerCorner>5.140242 45.398181</ows:LowerCorner>
                <ows:UpperCorner>11.47757 48.230651</ows:UpperCorner>
            </ows:WGS84BoundingBox>
            <Style>
                <ows:Identifier>default</ows:Identifier>
            </Style>
            <ResourceURL format="image/png" resourceType="tile" template="http://wmts/test_layer/{TileMatrix}/{TileCol}/{TileRow}.png"/>
        </Layer>
    </Contents>
</Capabilities>
"""


def test_publish_gwc_layer(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/gwc/rest/reload",
            status=200,
            match=[
                responses.matchers.urlencoded_params_matcher(
                    {"reload_configuration": "1"}
                )
            ],
        )
        rsps.get(
            url=f"{geoserver.url}/gwc/rest/layers/{WORKSPACE}:{LAYER}.json",
            status=404,
        )
        rsps.put(
            url=f"{geoserver.url}/gwc/rest/layers/{WORKSPACE}:{LAYER}.json",
            status=200,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "GeoServerLayer": {
                            "name": f"{WORKSPACE}:{LAYER}",
                            "enabled": "true",
                            "gridSubsets": {
                                "gridSubset": [{"gridSetName": f"EPSG:{EPSG}"}]
                            },
                        }
                    }
                )
            ],
        )

        response = geoserver.publish_gwc_layer(WORKSPACE, LAYER, EPSG)
        assert response
        assert response.status_code == 200


def test_publish_gwc_layer_already_exists(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/gwc/rest/reload",
            status=200,
            match=[
                responses.matchers.urlencoded_params_matcher(
                    {"reload_configuration": "1"}
                )
            ],
        )
        rsps.get(
            url=f"{geoserver.url}/gwc/rest/layers/{WORKSPACE}:{LAYER}.json",
            status=200,
            json={"GeoServerLayer": {"name": f"{WORKSPACE}:{LAYER}"}},
        )

        response = geoserver.publish_gwc_layer(WORKSPACE, LAYER, EPSG)
        assert response is None


def test_create_gridset(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/gwc/rest/gridsets/EPSG:{EPSG}.xml",
            status=404,
        )
        rsps.put(
            url=f"{geoserver.url}/gwc/rest/gridsets/EPSG:{EPSG}.xml",
            status=200,
        )

        response = geoserver.create_gridset(EPSG)
        assert response
        assert response.status_code == 200


def test_get_tile(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/gwc/service/wmts",
            status=200,
            body=CAPABILITIES,
            headers={"Content-Type": "application/xml"},
        )
        rsps.get(
            "http://wmts/test_layer/EPSG:3857:7/66/45.png",
            status=200,
            headers={"Content-Type": "image/png"},
        )

        response = geoserver.get_tile(
            format="image/png",
            layer=LAYER,
            tile_matrix_set="EPSG:3857",
            tile_matrix="EPSG:3857:7",
            column=66,
            row=45,
        )
        assert response
