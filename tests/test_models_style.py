from unittest.mock import Mock

import pytest

from geoservercloud.models import Style  # Adjust based on the actual import path


# Test initialization of Style class
def test_style_initialization():
    style = Style(
        name="test_style",
        workspace="test_workspace",
        format="sld",
        language_version={"version": "1.0.0"},
        filename="style.sld",
        date_created="2023-10-01",
        date_modified="2023-10-02",
        legend_url="http://example.com/legend.png",
        legend_format="image/png",
        legend_width="100",
        legend_height="100",
    )

    assert style.name == "test_style"
    assert style.workspace == "test_workspace"
    assert style.format == "sld"
    assert style.language_version == {"version": "1.0.0"}
    assert style.filename == "style.sld"
    assert style.date_created == "2023-10-01"
    assert style.date_modified == "2023-10-02"
    assert style.legend == {
        "onlineResource": "http://example.com/legend.png",
        "format": "image/png",
        "width": "100",
        "height": "100",
    }


# Test initialization without a legend
def test_style_initialization_without_legend():
    style = Style(
        name="test_style",
        workspace="test_workspace",
        format="sld",
        language_version={"version": "1.0.0"},
        filename="style.sld",
    )

    assert style.legend is None


# Test create_legend method
def test_style_create_legend():
    style = Style(
        name="test_style",
        workspace="test_workspace",
        legend_url="http://example.com/legend.png",
        legend_format="image/png",
        legend_width="100",
        legend_height="100",
    )

    assert style.legend == {
        "onlineResource": "http://example.com/legend.png",
        "format": "image/png",
        "width": "100",
        "height": "100",
    }


# Test put_payload method with legend
def test_style_put_payload_with_legend(mocker):
    style = Style(
        name="test_style",
        workspace="test_workspace",
        legend_url="http://example.com/legend.png",
        legend_format="image/png",
        legend_width="100",
        legend_height="100",
    )

    expected_payload = {
        "style": {
            "name": "test_style",
            "format": "sld",
            "languageVersion": {"version": "1.0.0"},
            "filename": None,
            "legend": {
                "onlineResource": "http://example.com/legend.png",
                "format": "image/png",
                "width": "100",
                "height": "100",
            },
        }
    }

    payload = style.put_payload()
    assert payload == expected_payload


# Test put_payload method without legend
def test_style_put_payload_without_legend(mocker):
    style = Style(
        name="test_style",
        workspace="test_workspace",
    )

    expected_payload = {
        "style": {
            "name": "test_style",
            "format": "sld",
            "languageVersion": {"version": "1.0.0"},
            "filename": None,
        }
    }

    payload = style.put_payload()
    assert payload == expected_payload


# Test post_payload method
def test_style_post_payload(mocker):
    style = Style(
        name="test_style",
        workspace="test_workspace",
    )

    mock_put_payload = mocker.patch.object(
        style, "put_payload", return_value={"style": {}}
    )

    payload = style.post_payload()

    assert payload == {"style": {}}
    mock_put_payload.assert_called_once()


# Test from_response method
def test_style_from_response():
    mock_response = Mock()
    mock_response.json.return_value = {
        "style": {
            "workspace": "test_workspace",
            "name": "test_style",
            "format": "sld",
            "languageVersion": {"version": "1.0.0"},
            "filename": "style.sld",
            "dateCreated": "2023-10-01",
            "dateModified": "2023-10-02",
            "legend": {
                "onlineResource": "http://example.com/legend.png",
                "format": "image/png",
                "width": "100",
                "height": "100",
            },
        }
    }

    style = Style.from_response(mock_response)

    assert style.name == "test_style"
    assert style.workspace == "test_workspace"
    assert style.format == "sld"
    assert style.language_version == {"version": "1.0.0"}
    assert style.filename == "style.sld"
    assert style.date_created == "2023-10-01"
    assert style.date_modified == "2023-10-02"
    assert style.legend == {
        "onlineResource": "http://example.com/legend.png",
        "format": "image/png",
        "width": "100",
        "height": "100",
    }
