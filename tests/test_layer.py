import responses

from geoservercloud import GeoServerCloud


def test_set_default_layer_style(geoserver: GeoServerCloud) -> None:
    workspace = "test_workspace"
    layer = "test_layer"
    style = "test_style"
    with responses.RequestsMock() as rsps:
        rsps.put(
            url=f"{geoserver.url}/rest/layers/{workspace}:{layer}.json",
            status=200,
            body=b"",
            match=[
                responses.matchers.json_params_matcher(
                    {"layer": {"name": layer, "defaultStyle": {"name": style}}}
                )
            ],
        )

        content, code = geoserver.set_default_layer_style(layer, workspace, style)

        assert content == ""
        assert code == 200
