import responses

from geoservercloud.geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

WORKSPACE = "test_workspace"
CAPABILITIES = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities version="1.1.0">
  <FeatureTypeList>
    <FeatureType>
      <Name>test_layer</Name>
    </FeatureType>
  </FeatureTypeList>
</wfs:WFS_Capabilities>
"""


def test_wfs(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{GEOSERVER_URL}/{WORKSPACE}/wfs",
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WFS",
                        "version": "1.1.0",
                        "request": "GetCapabilities",
                    }
                )
            ],
            body=CAPABILITIES,
            status=200,
        )

        response = geoserver.get_wfs_layers(WORKSPACE)

        assert response
        assert response == {"FeatureType": {"Name": "test_layer"}}
