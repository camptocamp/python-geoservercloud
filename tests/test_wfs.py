import responses

from geoservercloud import GeoServerCloud
from tests.conftest import GEOSERVER_URL

WORKSPACE = "test_workspace"
WFS_URL = f"{GEOSERVER_URL}/{WORKSPACE}/wfs"
CAPABILITIES = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities version="1.1.0">
  <FeatureTypeList>
    <FeatureType>
      <Name>test_layer</Name>
    </FeatureType>
  </FeatureTypeList>
</wfs:WFS_Capabilities>
"""
GET_PROPERTY_VALUE = f"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:ValueCollection xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:{WORKSPACE}="http://{WORKSPACE}"
    xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:ows="http://www.opengis.net/ows/1.1"
    xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/wfs/2.0 {GEOSERVER_URL}/schemas/wfs/2.0/wfs.xsd">
    <wfs:member><{WORKSPACE}:test_property>0</{WORKSPACE}:test_property></wfs:member>
</wfs:ValueCollection>"""
GET_PROPERTY_VALUE_LIST = f"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:ValueCollection xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:{WORKSPACE}="http://{WORKSPACE}"
    xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:ows="http://www.opengis.net/ows/1.1"
    xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/wfs/2.0 {GEOSERVER_URL}/schemas/wfs/2.0/wfs.xsd">
    <wfs:member><{WORKSPACE}:test_property>0</{WORKSPACE}:test_property></wfs:member>
    <wfs:member><{WORKSPACE}:test_property>1</{WORKSPACE}:test_property></wfs:member>
</wfs:ValueCollection>"""
GET_PROPERTY_VALUE_NO_FEATURE = f"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:ValueCollection xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:{WORKSPACE}="http://{WORKSPACE}"
    xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:ows="http://www.opengis.net/ows/1.1"
    xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/wfs/2.0 {GEOSERVER_URL}/schemas/wfs/2.0/wfs.xsd" />"""


def test_get_wfs_layers(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=WFS_URL,
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


def test_get_feature(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=WFS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WFS",
                        "version": "1.1.0",
                        "request": "GetFeature",
                        "typeName": "test_layer",
                        "outputFormat": "application/json",
                    }
                )
            ],
            status=200,
            json={"type": "FeatureCollection", "features": []},
        )

        feature = geoserver.get_feature(WORKSPACE, "test_layer")

        assert feature == {"type": "FeatureCollection", "features": []}


def test_describe_feature_type(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=WFS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WFS",
                        "version": "1.1.0",
                        "request": "DescribeFeatureType",
                        "typeName": "test_layer",
                        "outputFormat": "application/json",
                    }
                )
            ],
            status=200,
            json={"featureTypes": []},
        )

        feature_type = geoserver.describe_feature_type(WORKSPACE, "test_layer")

        assert feature_type == {"featureTypes": []}


def test_get_property_value_one_feature(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=WFS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WFS",
                        "version": "2.0.0",
                        "request": "GetPropertyValue",
                        "typeNames": "test_layer",
                        "valueReference": "test_property",
                    }
                )
            ],
            status=200,
            body=GET_PROPERTY_VALUE,
        )

        property = geoserver.get_property_value(
            WORKSPACE, "test_layer", "test_property"
        )

        assert property == {f"{WORKSPACE}:test_property": "0"}


def test_get_property_value_multiple_features(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=WFS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WFS",
                        "version": "2.0.0",
                        "request": "GetPropertyValue",
                        "typeNames": "test_layer",
                        "valueReference": "test_property",
                    }
                )
            ],
            status=200,
            body=GET_PROPERTY_VALUE_LIST,
        )

        property = geoserver.get_property_value(
            WORKSPACE, "test_layer", "test_property"
        )

        assert property == [
            {f"{WORKSPACE}:test_property": "0"},
            {f"{WORKSPACE}:test_property": "1"},
        ]


def test_get_property_value_no_feature(geoserver: GeoServerCloud) -> None:
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=WFS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "service": "WFS",
                        "version": "2.0.0",
                        "request": "GetPropertyValue",
                        "typeNames": "test_layer",
                        "valueReference": "test_property",
                    }
                )
            ],
            status=200,
            body=GET_PROPERTY_VALUE_NO_FEATURE,
        )

        property = geoserver.get_property_value(
            WORKSPACE, "test_layer", "test_property"
        )

        assert property == {}
