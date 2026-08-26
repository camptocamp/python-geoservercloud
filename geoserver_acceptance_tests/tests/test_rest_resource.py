"""Acceptance tests for the REST resource API (/rest/resource/**).

Regression coverage for https://github.com/geoserver/geoserver-cloud/issues/913:
requests whose path contains "/gwc" anywhere, such as /rest/resource/gwc-gs.xml,
used to fail with a 500 NPE ("Cannot invoke String.substring(int) because path
is null") or a 404 for existing resources, because the servlet filters that
rebuild getPathInfo() in GeoServer Cloud mistook them for GeoWebCache requests.
"""

import pytest

from geoservercloud import GeoServerCloud

RESOURCE_API = "/rest/resource"


@pytest.fixture
def rest_client(geoserver: GeoServerCloud):
    return geoserver.rest_service.rest_client


@pytest.fixture
def resource_directory(rest_client, request):
    """Factory for a resource directory deleted (recursively) on teardown."""

    def _create(directory_name):
        request.addfinalizer(
            lambda: rest_client.delete(f"{RESOURCE_API}/{directory_name}")
        )
        return directory_name

    return _create


def test_get_gwc_config_file(rest_client):
    """GET an existing file whose name contains "gwc": the exact request from issue #913."""
    response = rest_client.get(f"{RESOURCE_API}/gwc-gs.xml")
    assert response.status_code == 200
    assert "<GeoServerGWCConfig>" in response.text


def test_root_listing_contains_gwc_config_file(rest_client):
    response = rest_client.get(RESOURCE_API, params={"format": "json"})
    assert response.status_code == 200
    assert "gwc-gs.xml" in response.text


def test_nonexistent_gwc_prefixed_path_returns_404(rest_client):
    """Missing resources must report 404, not a 500 NPE (issue #913)."""
    response = rest_client.get(f"{RESOURCE_API}/gwcfoo")
    assert response.status_code == 404


def test_roundtrip_in_gwc_named_directory(rest_client, resource_directory):
    """Create, list, read and delete inside a directory whose name starts with "gwc"."""
    directory = resource_directory("gwc913dir")
    file_path = f"{RESOURCE_API}/{directory}/child.txt"

    put_text_resource(rest_client, file_path, "issue #913 directory probe")

    listing = rest_client.get(f"{RESOURCE_API}/{directory}", params={"format": "json"})
    assert listing.status_code == 200
    assert "child.txt" in listing.text

    assert_file_roundtrip(rest_client, file_path, "issue #913 directory probe")


def test_roundtrip_on_gwc_prefixed_file_name(rest_client, resource_directory):
    """Create, read and delete a file whose name starts with "gwc" (issue #913)."""
    directory = resource_directory("resource_api_913")
    file_path = f"{RESOURCE_API}/{directory}/gwc-913-probe.txt"

    put_text_resource(rest_client, file_path, "issue #913 file name probe")
    assert_file_roundtrip(rest_client, file_path, "issue #913 file name probe")


def test_roundtrip_on_plain_file_name(rest_client, resource_directory):
    """Baseline coverage of the resource API on a path without "gwc" in it."""
    directory = resource_directory("resource_api_plain")
    file_path = f"{RESOURCE_API}/{directory}/probe.txt"

    put_text_resource(rest_client, file_path, "plain resource probe")

    metadata = rest_client.get(
        file_path, params={"operation": "metadata", "format": "json"}
    )
    assert metadata.status_code == 200
    assert "probe.txt" in metadata.text

    assert_file_roundtrip(rest_client, file_path, "plain resource probe")


def put_text_resource(rest_client, file_path, contents):
    response = rest_client.put(
        file_path, data=contents, headers={"Content-Type": "text/plain"}
    )
    assert response.status_code in (200, 201)


def assert_file_roundtrip(rest_client, file_path, contents):
    """The file must be readable, deletable, and report 404 once deleted."""
    response = rest_client.get(file_path)
    assert response.status_code == 200
    assert response.text == contents

    response = rest_client.delete(file_path)
    assert response.status_code == 200

    response = rest_client.get(file_path)
    assert response.status_code == 404
