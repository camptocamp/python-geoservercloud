from pathlib import Path

import pytest
import responses
import responses.matchers
from requests import Response

from geoservercloud import GeoServerCloud
from geoservercloud.services.restclient import RestClient

STYLE = "test_style"


def test_get_styles_no_workspace(geoserver: GeoServerCloud):
    styles = [
        {
            "name": "style1",
            "href": f"{geoserver.url}/rest/styles/style1.json",
        },
        {
            "name": "style2",
            "href": f"{geoserver.url}/rest/styles/style2.json",
        },
    ]
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles.json",
            status=200,
            json={"styles": {"style": styles}},
        )
        content, code = geoserver.get_styles()

    assert content == styles
    assert code == 200


def test_get_styles_with_workspace(geoserver: GeoServerCloud):
    workspace_name = "test_workspace"
    styles = [
        {
            "name": "style3",
            "href": f"{geoserver.url}/rest/workspaces/{workspace_name}/styles/style3.json",
        },
        {
            "name": "style4",
            "href": f"{geoserver.url}/rest/workspaces/{workspace_name}/styles/style4.json",
        },
    ]
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/styles.json",
            status=200,
            json={"styles": {"style": styles}},
        )
        content, code = geoserver.get_styles(workspace_name)

    assert content == styles
    assert code == 200


def test_get_style_definition_no_workspace(geoserver: GeoServerCloud):
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles/{STYLE}.json",
            status=200,
            json={
                "style": {
                    "name": STYLE,
                    "format": "sld",
                    "languageVersion": {"version": "1.0.0"},
                    "filename": f"{STYLE}.sld",
                }
            },
        )
        content, code = geoserver.get_style_definition(STYLE)

    assert content == {
        "name": STYLE,
        "format": "sld",
        "languageVersion": {"version": "1.0.0"},
        "filename": f"{STYLE}.sld",
    }
    assert code == 200


def test_get_style_definition_with_workspace(geoserver: GeoServerCloud):
    workspace_name = "test_workspace"
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/{workspace_name}/styles/{STYLE}.json",
            status=200,
            json={
                "style": {
                    "name": STYLE,
                    "workspace": {"name": workspace_name},
                    "format": "sld",
                    "languageVersion": {"version": "1.0.0"},
                    "filename": f"{STYLE}.sld",
                }
            },
        )
        content, code = geoserver.get_style_definition(STYLE, workspace_name)

    assert content == {
        "name": STYLE,
        "format": "sld",
        "languageVersion": {"version": "1.0.0"},
        "filename": f"{STYLE}.sld",
        "workspace": workspace_name,
    }
    assert code == 200


def test_create_style_definition(mocker, geoserver: GeoServerCloud) -> None:
    # Use mocker to check the POST request payload (binary payload matching is not supported by responses)
    response = Response()
    response.status_code = 201
    response._content = b"test_style"
    mock_post = mocker.patch.object(
        geoserver.rest_service.rest_client, "post", return_value=response
    )
    expected_xml = """
    <style>
        <name>test_style</name>
        <format>sld</format>
        <languageVersion><version>1.0.0</version></languageVersion>
        <workspace><name>test_workspace</name></workspace>
        <filename>style.sld</filename>
    </style>
    """
    expected_payload: bytes = "".join(expected_xml.split()).encode("utf-8")
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/workspaces/test_workspace/styles/{STYLE}",
            status=404,
            match=[responses.matchers.header_matcher({"Accept": "application/json"})],
        )
        geoserver.create_style_definition(
            style_name=STYLE, filename="style.sld", workspace_name="test_workspace"
        )
        mock_post.assert_called_with(
            "/rest/workspaces/test_workspace/styles",
            data=expected_payload,
            headers={"Content-Type": "text/xml"},
        )


def test_create_style_from_string(geoserver: GeoServerCloud) -> None:
    style_string = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <StyledLayerDescriptor>
        <NamedLayer>
            <Name>test_layer</Name>
            <UserStyle>
                <Title>Test Style</Title>
                <FeatureTypeStyle>
                    <Rule>
                        <Name>rule1</Name>
                        <Title>Rule 1</Title>
                        <PolygonSymbolizer>
                            <Fill>
                                <CssParameter name="fill">#FF0000</CssParameter>
                            </Fill>
                        </PolygonSymbolizer>
                    </Rule>
                </FeatureTypeStyle>
            </UserStyle>
        </NamedLayer>
    </StyledLayerDescriptor>
    """
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}.sld",
            status=201,
            body=b"test_style",
            match=[
                responses.matchers.header_matcher(
                    {"Content-Type": "application/vnd.ogc.sld+xml"}
                )
            ],
            # Matching of body content as string is not supported by responses
        )

        content, code = geoserver.create_style_from_string(
            style_name=STYLE,
            style_string=style_string,
        )

        assert content == STYLE
        assert code == 201


def test_create_style_from_file(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.sld").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}.sld",
            status=201,
            body=b"test_style",
            match=[
                responses.matchers.header_matcher(
                    {"Content-Type": "application/vnd.ogc.sld+xml"}
                )
            ],
            # Matching of binary content is not supported by responses
        )

        content, code = geoserver.create_style_from_file(
            style_name=STYLE,
            file=str(file_path),
        )

        assert content == STYLE
        assert code == 201


def test_update_style_from_file(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.sld").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}.sld",
            status=200,
            body=b"",
            match=[
                responses.matchers.header_matcher(
                    {"Content-Type": "application/vnd.ogc.sld+xml"}
                )
            ],
            # Matching of binary content is not supported by responses
        )

        content, code = geoserver.create_style_from_file(
            style_name=STYLE,
            file=str(file_path),
        )

        assert content == ""
        assert code == 200


def test_create_style_from_file_mbstyle(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.mbstyle").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}.mbstyle",
            status=201,
            body=b"test_style",
            match=[
                responses.matchers.header_matcher(
                    {"Content-Type": "application/vnd.geoserver.mbstyle+json"}
                )
            ],
        )
        content, code = geoserver.create_style_from_file(
            style_name=STYLE,
            file=str(file_path),
        )

        assert content == STYLE
        assert code == 201


def test_create_style_from_file_zip(geoserver: GeoServerCloud) -> None:
    file_path = (Path(__file__).parent / "resources/style.zip").resolve()
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=200,
        )
        rsps.put(
            url=f"{geoserver.url}/rest/styles/{STYLE}",
            status=201,
            body=b"test_style",
            match=[
                responses.matchers.header_matcher({"Content-Type": "application/zip"})
            ],
            # Matching of binary content is not supported by responses
        )

        content, code = geoserver.create_style_from_file(
            style_name=STYLE,
            file=str(file_path),
        )

        assert content == STYLE
        assert code == 201


def test_create_style_from_file_unsupported_format(geoserver: GeoServerCloud) -> None:
    with pytest.raises(ValueError) as excinfo:
        geoserver.create_style_from_file(
            style_name=STYLE,
            file="resources/style.txt",
        )
    assert "Unsupported file extension" in str(excinfo.value)
