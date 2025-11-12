import responses
import responses.matchers

from geoservercloud.geoservercloud import GeoServerCloud


def mock_coverage_store(workspace: str, store: str) -> dict:
    return {
        "name": store,
        "type": "ImageMosaic",
        "enabled": True,
        "workspace": {
            "name": workspace,
            "href": f"http://localhost:8080/geoserver/rest/workspaces/{workspace}.json",
        },
        "_default": False,
        "dateCreated": "2025-11-10 13:30:23.544 UTC",
        "disableOnConnFailure": False,
        "url": "/opt/geoserver_data/sampledata/ne/pyramid/",
        "coverages": f"http://localhost:8080/geoserver/rest/workspaces/{workspace}/coveragestores/{store}/coverages.json",
    }


def test_get_coverage_store(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"
    coveragestore = mock_coverage_store(workspace_name, coveragestore_name)

    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"http://localhost:8080/geoserver/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}.json",
            status=200,
            json={"coverageStore": coveragestore},
        )
        content, code = geoserver.get_coverage_store(workspace_name, coveragestore_name)
        assert isinstance(content, dict)
        assert code == 200
        assert content.get("name") == coveragestore_name
        assert content.get("workspace") == workspace_name
        assert content.get("type") == "ImageMosaic"
        assert content.get("enabled") is True
        assert content.get("url") == "/opt/geoserver_data/sampledata/ne/pyramid/"
        assert (
            content.get("coverages")
            == f"http://localhost:8080/geoserver/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages.json"
        )
        assert content.get("dateCreated") == "2025-11-10 13:30:23.544 UTC"
        assert content.get("disableOnConnFailure") is False
        assert content.get("_default") is False


def test_create_coverage_store(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"
    store_type = "GeoTIFF"
    url = "cog://http://example"
    post_payload = {
        "coverageStore": {
            "name": coveragestore_name,
            "workspace": {
                "name": workspace_name,
            },
            "type": store_type,
            "enabled": True,
            "url": url,
            "metadata": {
                "entry": {
                    "@key": "CogSettings.Key",
                    "cogSettings": {"rangeReaderSettings": "HTTP"},
                }
            },
        }
    }

    with responses.RequestsMock() as rsps:
        rsps.post(
            url=f"http://localhost:8080/geoserver/rest/workspaces/{workspace_name}/coveragestores.json",
            status=201,
            body=b"test_coveragestore_name",
            match=[responses.matchers.json_params_matcher(post_payload)],
        )
        content, code = geoserver.create_coverage_store(
            workspace_name=workspace_name,
            coveragestore_name=coveragestore_name,
            type=store_type,
            url=url,
            metadata={"cogSettings": {"rangeReaderSettings": "HTTP"}},
        )
        assert content == coveragestore_name


def test_create_coverage_store_from_directory(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"
    directory_path = "/mnt/path/to/data/"

    with responses.RequestsMock() as rsps:
        rsps.put(
            f"http://localhost:8080/geoserver/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/external.imagemosaic",
            status=201,
            json={
                "coverageStore": {
                    "name": coveragestore_name,
                    "workspace": {"name": workspace_name},
                    "type": "ImageMosaic",
                    "enabled": True,
                    "url": "file:/mnt/path/to/data/",
                    "_default": False,
                    "disableOnConnFailure": False,
                }
            },
            match=[
                responses.matchers.header_matcher(
                    {"Content-Type": "text/plain", "Accept": "application/json"}
                )
            ],
        )
        content, code = geoserver.create_imagemosaic_store_from_directory(
            workspace_name=workspace_name,
            coveragestore_name=coveragestore_name,
            directory_path=directory_path,
        )
        assert code == 201
        assert content == coveragestore_name


def test_create_imagemosaic_store_from_properties_zip(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"
    zip_content = b"some properties"

    with responses.RequestsMock() as rsps:
        rsps.put(
            f"http://localhost:8080/geoserver/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/file.imagemosaic?configure=none",
            status=201,
            body="",
            match=[
                responses.matchers.header_matcher(
                    {"Content-Type": "application/zip", "Accept": "application/json"}
                )
            ],
        )
        content, code = geoserver.create_imagemosaic_store_from_properties_zip(
            workspace_name=workspace_name,
            coveragestore_name=coveragestore_name,
            properties_zip=zip_content,
        )
        assert code == 201
        assert content == ""


def test_delete_coverage_store(geoserver: GeoServerCloud):
    workspace_name = "test_coverage_ws"
    coveragestore_name = "test_coveragestore_name"

    with responses.RequestsMock() as rsps:
        rsps.delete(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/coveragestores/{coveragestore_name}.json?recurse=true",
            status=200,
            body="",
        )
        content, code = geoserver.delete_coverage_store(
            workspace_name, coveragestore_name
        )
        assert content == ""
        assert code == 200
