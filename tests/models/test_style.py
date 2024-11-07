from geoservercloud.models.style import Style


def test_style_initialization():
    style = Style(
        name="test_style",
        workspace_name="test_workspace",
        format="sld",
        language_version={"version": "1.0.0"},
        filename="style.sld",
        date_created="2023-10-01",
        date_modified="2023-10-02",
        legend_url="http://example.com/legend.png",
        legend_format="image/png",
        legend_width=100,
        legend_height=100,
    )

    assert style.name == "test_style"
    assert style.workspace_name == "test_workspace"
    assert style.format == "sld"
    assert style.language_version == {"version": "1.0.0"}
    assert style.filename == "style.sld"
    assert style.date_created == "2023-10-01"
    assert style.date_modified == "2023-10-02"
    assert style.legend == {
        "onlineResource": "http://example.com/legend.png",
        "format": "image/png",
        "width": 100,
        "height": 100,
    }


def test_style_initialization_without_legend():
    style = Style(
        name="test_style",
        workspace_name="test_workspace",
        format="sld",
        language_version={"version": "1.0.0"},
        filename="style.sld",
    )

    assert style.legend is None


def test_style_put_payload_with_legend():
    style = Style(
        name="test_style",
        workspace_name="test_workspace",
        legend_url="http://example.com/legend.png",
        legend_format="image/png",
        legend_width=100,
        legend_height=100,
    )

    expected_payload = {
        "style": {
            "name": "test_style",
            "format": "sld",
            "languageVersion": {"version": "1.0.0"},
            "legend": {
                "onlineResource": "http://example.com/legend.png",
                "format": "image/png",
                "width": 100,
                "height": 100,
            },
            "workspace": {"name": "test_workspace"},
        }
    }

    assert style.put_payload() == expected_payload


def test_style_put_payload_without_legend(mocker):
    style = Style(
        name="test_style",
        workspace_name="test_workspace",
    )

    expected_payload = {
        "style": {
            "name": "test_style",
            "format": "sld",
            "languageVersion": {"version": "1.0.0"},
            "workspace": {"name": "test_workspace"},
        }
    }

    assert style.put_payload() == expected_payload


def test_style_put_payload(mocker):
    style = Style(
        name="test_style",
        workspace_name="test_workspace",
    )

    mock_put_payload = mocker.patch.object(
        style, "post_payload", return_value={"style": {}}
    )

    payload = style.put_payload()

    assert payload == {"style": {}}
    mock_put_payload.assert_called_once()


def test_style_from_get_response_payload():
    mock_response = {
        "style": {
            "workspace": {"name": "test_workspace"},
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

    style = Style.from_get_response_payload(mock_response)

    assert style.name == "test_style"
    assert style.workspace_name == "test_workspace"
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
