import responses
import responses.matchers

from geoservercloud import GeoServerCloud


def mock_coverage(workspace, store, coverage):
    return {
        "coverage": {
            "name": coverage,
            "nativeName": coverage,
            "namespace": {
                "name": workspace,
                "href": f"http://localhost:8080/geoserver/rest/namespaces/{workspace}.json",
            },
            "title": f"Title {coverage}",
            "description": "Generated from ImageMosaic",
            "keywords": {"string": ["pyramid", "WCS", "ImageMosaic"]},
            "nativeCRS": 'GEOGCS["WGS 84", \n  DATUM["World Geodetic System 1984", \n    SPHEROID["WGS 84", 6378137.0, 298.257223563, AUTHORITY["EPSG","7030"]], \n    AUTHORITY["EPSG","6326"]], \n  PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]], \n  UNIT["degree", 0.017453292519943295], \n  AXIS["Geodetic longitude", EAST], \n  AXIS["Geodetic latitude", NORTH], \n  AUTHORITY["EPSG","4326"]]',
            "srs": "EPSG:4326",
            "nativeBoundingBox": {
                "minx": -180,
                "maxx": 180,
                "miny": -90,
                "maxy": 90,
                "crs": "EPSG:4326",
            },
            "latLonBoundingBox": {
                "minx": -180,
                "maxx": 180,
                "miny": -90,
                "maxy": 90,
                "crs": "EPSG:4326",
            },
            "projectionPolicy": "REPROJECT_TO_DECLARED",
            "enabled": True,
            "metadata": {"entry": {"@key": "dirName", "$": "ne_pyramid_store_null"}},
            "store": {
                "@class": "coverageStore",
                "name": f"{workspace}:{store}",
                "href": f"http://localhost:8080/geoserver/rest/workspaces/{workspace}/coveragestores/{store}.json",
            },
            "serviceConfiguration": False,
            "simpleConversionEnabled": False,
            "nativeFormat": "ImageMosaic",
            "grid": {
                "@dimension": 2,
                "range": {"low": "0 0", "high": "8099 4049"},
                "transform": {
                    "scaleX": 0.04444444444444,
                    "scaleY": -0.04444444444444,
                    "shearX": 0,
                    "shearY": 0,
                    "translateX": -179.9777777777778,
                    "translateY": 89.97777777777777,
                },
                "crs": "EPSG:4326",
            },
            "supportedFormats": {
                "string": [
                    "ArcGrid",
                    "ImageMosaic",
                    "GEOTIFF",
                    "GIF",
                    "PNG",
                    "JPEG",
                    "TIFF",
                    "GeoPackage (mosaic)",
                ]
            },
            "interpolationMethods": {
                "string": ["nearest neighbor", "bilinear", "bicubic"]
            },
            "defaultInterpolationMethod": "nearest neighbor",
            "dimensions": {
                "coverageDimension": [
                    {
                        "name": "RED_BAND",
                        "description": "GridSampleDimension[-Infinity,Infinity]",
                        "range": {"min": "-inf", "max": "inf"},
                        "nullValues": {"double": 0},
                        "unit": "W.m-2.Sr-1",
                        "dimensionType": {"name": "UNSIGNED_8BITS"},
                    },
                    {
                        "name": "GREEN_BAND",
                        "description": "GridSampleDimension[-Infinity,Infinity]",
                        "range": {"min": "-inf", "max": "inf"},
                        "nullValues": {"double": 0},
                        "unit": "W.m-2.Sr-1",
                        "dimensionType": {"name": "UNSIGNED_8BITS"},
                    },
                    {
                        "name": "BLUE_BAND",
                        "description": "GridSampleDimension[-Infinity,Infinity]",
                        "range": {"min": "-inf", "max": "inf"},
                        "nullValues": {"double": 0},
                        "unit": "W.m-2.Sr-1",
                        "dimensionType": {"name": "UNSIGNED_8BITS"},
                    },
                ]
            },
            "requestSRS": {"string": "EPSG:4326"},
            "responseSRS": {"string": "EPSG:4326"},
            "parameters": {
                "entry": [
                    {"string": ["BackgroundValues", ""]},
                    {"string": ["OVERVIEW_POLICY", "QUALITY"]},
                ]
            },
            "nativeCoverageName": coverage,
        }
    }


def test_get_coverages(geoserver: GeoServerCloud) -> None:
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coverage_store"
    coverages = {
        "coverages": {
            "coverage": [
                {
                    "name": "pyramid",
                    "href": f"http://localhost/geoserver/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages/pyramid.json",
                }
            ]
        }
    }
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages.json",
            status=200,
            json=coverages,
        )

        content, code = geoserver.get_coverages(workspace_name, coveragestore_name)

        assert isinstance(content, list)
        assert content[0].get("name") == "pyramid"
        assert code == 200

    crazy_coverages = {"list": {"string": ["manual_granules_coverage"]}}
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages.json",
            status=200,
            json=crazy_coverages,
        )

        content, code = geoserver.get_coverages(workspace_name, coveragestore_name)
        assert isinstance(content, list)
        assert content[0].get("name") == "manual_granules_coverage"
        assert code == 200


def test_get_coverage(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"
    coverage = "test_coverage_name"

    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages/{coverage}.json",
            status=200,
            json=mock_coverage(workspace_name, coveragestore_name, coverage),
        )
        content, code = geoserver.get_coverage(
            workspace_name, coveragestore_name, coverage
        )
        assert isinstance(content, dict)
        assert code == 200
        assert content.get("name") == coverage
        assert content.get("title") == f"Title {coverage}"
        assert content.get("nativeName") == coverage
        assert content.get("enabled") is True


def test_create_coverage(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"
    coverage_name = "test_coverage_name"
    native_name = "native_coverage_name"
    title = "Test Coverage Title"

    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages.json",
            status=201,
            body=coverage_name,
            match=[
                responses.matchers.json_params_matcher(
                    {
                        "coverage": {
                            "name": coverage_name,
                            "title": title,
                            "nativeName": native_name,
                            "store": {"name": f"{workspace_name}:{coveragestore_name}"},
                            "enabled": True,
                        }
                    }
                )
            ],
        )
        content, code = geoserver.create_coverage(
            workspace_name,
            coveragestore_name,
            coverage_name,
            title=title,
            native_name=native_name,
        )
        assert isinstance(content, str)
        assert content == coverage_name
        assert code == 201
