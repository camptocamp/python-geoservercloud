import responses

from geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

WORKSPACE = "test_workspace"
LAYER = "test_layer"
BBOX = (5.140242, 45.398181, 11.47757, 48.230651)
WIDTH = 768
HEIGHT = 330
FORMAT = "image/jpeg"
CAPABILITIES = f"""<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms" xmlns:xlink="http://www.w3.org/1999/xlink">
    <Service>
        <Name>WMS</Name>
        <Title>GeoServer Web Map Service</Title>
    </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>text/xml</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xlink:type="simple" xlink:href="{GEOSERVER_URL}/wms"/>
            </Get>
          </HTTP>
        </DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <Format>image/jpeg</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xlink:type="simple" xlink:href="{GEOSERVER_URL}/wms"/>
            </Get>
          </HTTP>
        </DCPType>
      </GetMap>
      <GetFeatureInfo>
        <Format>text/xml</Format>
        <Format>text/plain</Format>
        <Format>text/html</Format>
        <DCPType>
          <HTTP>
            <Get>
              <OnlineResource xlink:type="simple" xlink:href="{GEOSERVER_URL}/wms"/>
            </Get>
          </HTTP>
        </DCPType>
      </GetFeatureInfo>
    </Request>
    <Layer>
      <Name>test_layer</Name>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""


def test_get_layers(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/{WORKSPACE}/wms",
            status=200,
            headers={"Content-Type": "text/xml"},
            body=CAPABILITIES,
            match=[
                responses.matchers.query_param_matcher(
                    {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"}
                )
            ],
        )

        layers = geoserver.get_wms_layers(WORKSPACE)
        assert layers == {"Name": "test_layer"}


def test_get_map(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/wms",
            status=200,
            headers={"Content-Type": "text/xml"},
            body=CAPABILITIES,
            match=[
                responses.matchers.query_param_matcher(
                    {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"}
                )
            ],
        )
        rsps.get(
            f"{geoserver.url}/wms",
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WMS",
                        "request": "GetMap",
                        "version": "1.3.0",
                        "bbox": f"{BBOX[1]},{BBOX[0]},{BBOX[3]},{BBOX[2]}",
                        "layers": LAYER,
                        "width": WIDTH,
                        "height": HEIGHT,
                        "format": FORMAT,
                        "transparent": "TRUE",
                        "crs": "EPSG:4326",
                        "exceptions": "XML",
                        "bgcolor": "0xFFFFFF",
                    }
                )
            ],
            status=200,
        )

        geoserver.create_wms()
        geoserver.get_map(
            layers=[LAYER],
            bbox=BBOX,
            size=(WIDTH, HEIGHT),
            format=FORMAT,
            srs="EPSG:4326",
        )


def test_get_feature_info(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/wms",
            status=200,
            headers={"Content-Type": "text/xml"},
            body=CAPABILITIES,
            match=[
                responses.matchers.query_param_matcher(
                    {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"}
                )
            ],
        )
        rsps.get(
            f"{geoserver.url}/wms",
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WMS",
                        "request": "GetFeatureInfo",
                        "version": "1.3.0",
                        "bbox": f"{BBOX[1]},{BBOX[0]},{BBOX[3]},{BBOX[2]}",
                        "layers": LAYER,
                        "query_layers": LAYER,
                        "width": WIDTH,
                        "height": HEIGHT,
                        "info_format": "text/xml",
                        "transparent": "TRUE",
                        "crs": "EPSG:4326",
                        "format": "None",
                        "i": 0,
                        "j": 0,
                        "feature_count": 20,
                        "exceptions": "XML",
                        "bgcolor": "0xFFFFFF",
                    }
                )
            ],
            status=200,
        )

        geoserver.create_wms()
        geoserver.get_feature_info(
            layers=[LAYER],
            bbox=BBOX,
            size=(WIDTH, HEIGHT),
            srs="EPSG:4326",
            info_format="text/xml",
        )


def test_get_legend(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            f"{geoserver.url}/wms",
            status=200,
            headers={"Content-Type": "text/xml"},
            body=CAPABILITIES,
            match=[
                responses.matchers.query_param_matcher(
                    {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"}
                )
            ],
        )
        rsps.get(
            f"{geoserver.url}/wms",
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WMS",
                        "request": "GetLegendGraphic",
                        "version": "1.3.0",
                        "layer": LAYER,
                        "format": FORMAT,
                    }
                )
            ],
            status=200,
        )

        geoserver.create_wms()
        geoserver.get_legend_graphic(
            layer=[LAYER],
            format=FORMAT,
        )


def test_set_default_locale_for_service(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.put(
            f"{geoserver.url}/rest/services/wms/workspaces/{WORKSPACE}/settings.json",
            status=200,
            body=b"",
            match=[
                responses.matchers.json_params_matcher({"wms": {"defaultLocale": "en"}})
            ],
        )

        content, code = geoserver.set_default_locale_for_service(WORKSPACE, "en")
        assert content == ""
        assert code == 200
