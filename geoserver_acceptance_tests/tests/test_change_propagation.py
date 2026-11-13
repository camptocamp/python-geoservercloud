"""Changes made through one GeoServer Cloud service reach the other services.

The services share the catalog, the configuration and the resource store, and
each one keeps what it read in memory. A change made through the REST API runs
on the restconfig service, and the wms and gwc services learn about it from the
event bus. These tests write through REST, read through WMS and WMTS, and poll
for the new state. Against a single GeoServer the first poll already settles.

Regression coverage for https://github.com/geoserver/geoserver-cloud/issues/1074.
"""

import time
import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import pytest
import requests
import xmltodict
from sqlalchemy import text

from geoservercloud import GeoServerCloud

# how long a change may take to reach another service
PROPAGATION_TIMEOUT = 30
# a lookup finding nothing is remembered for 30 s by the pgconfig cache; a
# layer created after such a lookup must show up well before that
MISS_TIMEOUT = 20

RED = "#ff0000"
BLUE = "#0000ff"
RGB = {RED: (255, 0, 0), BLUE: (0, 0, 255)}

POINT = (10.0, 10.0)
BBOX = (9.5, 9.5, 10.5, 10.5)
IMAGE_SIZE = 16
# a square this big covers the whole GetMap image, so the top-left pixel has the fill color
COVERING_SIZE = 200
SLD_CONTENT_TYPE = {"Content-Type": "application/vnd.ogc.sld+xml"}
XML_CONTENT_TYPE = {"Content-Type": "text/xml"}


def point_sld(color: str, size: int) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink">
  <NamedLayer><Name>point</Name><UserStyle><FeatureTypeStyle><Rule>
    <PointSymbolizer><Graphic>
      <Mark><WellKnownName>square</WellKnownName>
        <Fill><CssParameter name="fill">{color}</CssParameter></Fill></Mark>
      <Size>{size}</Size>
    </Graphic></PointSymbolizer>
  </Rule></FeatureTypeStyle></UserStyle></NamedLayer>
</StyledLayerDescriptor>"""


def wait_until(
    condition: Callable[[], bool], timeout: float = PROPAGATION_TIMEOUT
) -> bool:
    """Polls the condition every half second until it holds or the timeout passes."""
    deadline = time.monotonic() + timeout
    while True:
        if condition():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.5)


def http_get(
    geoserver: GeoServerCloud, path: str, params: dict[str, Any] | None = None
) -> requests.Response:
    """GET of a path of the server, returned whatever its status code."""
    return requests.get(
        f"{geoserver.url}{path}", params=params, auth=geoserver.auth, timeout=60
    )


def is_image(response, mime_type: str = "image/png") -> bool:
    content_type = response.headers.get("Content-Type", "")
    return response.status_code == 200 and content_type.startswith(mime_type)


def first_pixel(png: bytes) -> tuple[int, ...]:
    """The RGB of the top-left pixel of a PNG, read without an image library.

    The PNG filters leave the first pixel of the first scanline unchanged, so it
    needs no unfiltering. Palette images are resolved through their palette.
    """
    assert png[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    position = 8
    idat = b""
    palette = b""
    color_type = -1
    while position < len(png):
        length = int.from_bytes(png[position : position + 4], "big")
        kind = png[position + 4 : position + 8]
        data = png[position + 8 : position + 8 + length]
        if kind == b"IHDR":
            bit_depth, color_type, interlace = data[8], data[9], data[12]
            assert bit_depth == 8 and interlace == 0, "unsupported PNG layout"
        elif kind == b"PLTE":
            palette = data
        elif kind == b"IDAT":
            idat += data
        elif kind == b"IEND":
            break
        position += 12 + length
    first_row = zlib.decompress(idat)
    if color_type == 3:
        index = first_row[1]
        return tuple(palette[3 * index : 3 * index + 3])
    return tuple(first_row[1:4])


def wms_layers(capabilities: dict[str, Any]) -> Iterator[tuple[str, list[str]]]:
    """Yields (name, names of the direct children) for the named layers of a WMS 1.3.0 capabilities document."""

    def as_list(node: Any) -> list[dict[str, Any]]:
        if node is None:
            return []
        return node if isinstance(node, list) else [node]

    def walk(layer: dict[str, Any]) -> Iterator[tuple[str, list[str]]]:
        children = as_list(layer.get("Layer"))
        if "Name" in layer:
            yield layer["Name"], [
                child["Name"] for child in children if "Name" in child
            ]
        for child in children:
            yield from walk(child)

    yield from walk(capabilities["WMS_Capabilities"]["Capability"]["Layer"])


def wmts_layer_names(capabilities_xml: bytes) -> list[str]:
    contents = xmltodict.parse(capabilities_xml)["Capabilities"]["Contents"]
    layers = contents.get("Layer", [])
    layers = layers if isinstance(layers, list) else [layers]
    return [layer["ows:Identifier"] for layer in layers]


def local_name(name: str) -> str:
    return name.split(":")[-1]


@dataclass
class PointLayer:
    """A workspace with a PostGIS feature type holding one point at POINT."""

    geoserver: GeoServerCloud
    workspace: str
    datastore: str
    name: str
    config: dict
    db_session: Any

    @property
    def prefixed_name(self) -> str:
        return f"{self.workspace}:{self.name}"

    @property
    def rest(self):
        return self.geoserver.rest_service.rest_client

    def create(self) -> None:
        attributes = {"geom": {"type": "Point", "required": True}}
        _, code = self.geoserver.create_feature_type(
            self.name, attributes=attributes, epsg=4326, workspace_name=self.workspace
        )
        assert code == 201
        table = f"{self.config['db']['pg_schema']}.{self.name}"
        self.db_session.execute(
            text(
                f"INSERT INTO {table} (geom) VALUES (public.ST_SetSRID(public.ST_MakePoint(:x, :y), 4326))"
            ),
            {"x": POINT[0], "y": POINT[1]},
        )
        self.db_session.commit()

    def get_map(self, workspace: str | None = "", layers: str | None = None):
        """GetMap of the point, through the workspace service by default, or the global one with workspace=None."""
        path = "/wms" if workspace is None else f"/{self.workspace}/wms"
        params = {
            "service": "WMS",
            "version": "1.1.1",
            "request": "GetMap",
            "layers": layers or self.name,
            "styles": "",
            "srs": "EPSG:4326",
            "bbox": ",".join(str(coordinate) for coordinate in BBOX),
            "width": IMAGE_SIZE,
            "height": IMAGE_SIZE,
            "format": "image/png",
            "transparent": "false",
        }
        return http_get(self.geoserver, path, params)

    def get_tile(self, mime_type: str = "image/png", workspace: str | None = None):
        """GetTile of the zoom 1 tile holding the point, through the global WMTS or the workspace one."""
        path = (
            "/gwc/service/wmts"
            if workspace is None
            else f"/{workspace}/gwc/service/wmts"
        )
        layer = self.prefixed_name if workspace is None else self.name
        params = {
            "service": "WMTS",
            "version": "1.0.0",
            "request": "GetTile",
            "layer": layer,
            "style": "",
            "tilematrixset": "EPSG:4326",
            "tilematrix": "EPSG:4326:1",
            "tilerow": 0,
            "tilecol": 2,
            "format": mime_type,
        }
        return http_get(self.geoserver, path, params)

    def wait_for_tile_layer(self) -> None:
        assert wait_until(
            lambda: self.geoserver.get_gwc_layer(self.workspace, self.name)[1] == 200
        ), "tile layer not created"

    def set_enabled(self, enabled: bool) -> None:
        """Enables or disables the feature type of the layer; a layer is served only while its resource is enabled."""
        response = self.rest.put(
            f"/rest/workspaces/{self.workspace}/datastores/{self.datastore}/featuretypes/{self.name}.json",
            json={"featureType": {"enabled": enabled}},
        )
        assert response.status_code == 200

    def create_style(self, style: str, sld: str) -> None:
        _, code = self.geoserver.create_style_from_string(style, sld, self.workspace)
        assert code in (200, 201)

    def use_style(self, style: str, sld: str) -> None:
        self.create_style(style, sld)
        _, code = self.geoserver.set_default_layer_style(
            self.name, self.workspace, style
        )
        assert code == 200

    def update_style(self, style: str, sld: str) -> None:
        response = self.rest.put(
            f"/rest/workspaces/{self.workspace}/styles/{style}",
            data=sld,
            headers=SLD_CONTENT_TYPE,
        )
        assert response.status_code == 200

    def map_color(self) -> tuple[int, ...] | None:
        response = self.get_map()
        if not is_image(response):
            return None
        return first_pixel(response.content)

    def wms_capabilities(self) -> dict[str, Any]:
        return self.geoserver.ows_service.get_wms_capabilities(self.workspace)


@pytest.fixture
def point_layer(config, db_session, geoserver_factory):
    """Factory of a workspace with a PostGIS store and, unless told otherwise, one point layer."""

    def _create(
        workspace: str, layer: str = "point", create_layer: bool = True
    ) -> PointLayer:
        geoserver: GeoServerCloud = geoserver_factory(workspace)
        _, code = geoserver.create_pg_datastore(
            workspace_name=workspace,
            datastore_name=workspace,
            pg_host=config["db"]["pg_host"]["docker"],
            pg_port=config["db"]["pg_port"]["docker"],
            pg_db=config["db"]["pg_db"],
            pg_user=config["db"]["pg_user"],
            pg_password=config["db"]["pg_password"],
            pg_schema=config["db"]["pg_schema"],
            set_default_datastore=True,
        )
        assert code == 201
        point = PointLayer(geoserver, workspace, workspace, layer, config, db_session)
        if create_layer:
            point.create()
        return point

    return _create


@pytest.mark.db
def test_disabled_layer_stops_serving(point_layer):
    """A feature type disabled through REST stops answering GetMap and GetTile on the other services."""
    point = point_layer("test_propagation_disabled")
    point.wait_for_tile_layer()
    assert wait_until(lambda: is_image(point.get_map()))
    assert wait_until(lambda: is_image(point.get_tile()))

    point.set_enabled(False)
    assert wait_until(
        lambda: not is_image(point.get_map())
    ), "GetMap still serves the disabled layer"
    assert wait_until(
        lambda: not is_image(point.get_tile())
    ), "GetTile still serves the disabled layer"

    point.set_enabled(True)
    assert wait_until(lambda: is_image(point.get_map()))
    assert wait_until(lambda: is_image(point.get_tile()))


@pytest.mark.db
def test_layer_created_after_a_miss(point_layer):
    """A layer requested before it exists is served soon after its creation through REST."""
    point = point_layer("test_propagation_miss", layer="late", create_layer=False)
    assert not is_image(point.get_map())
    assert not is_image(point.get_tile())

    point.create()

    assert wait_until(
        lambda: is_image(point.get_map()), MISS_TIMEOUT
    ), "GetMap keeps the miss"
    assert wait_until(
        lambda: is_image(point.get_tile()), MISS_TIMEOUT
    ), "GetTile keeps the miss"


@pytest.mark.db
def test_style_change_reaches_getmap(point_layer):
    """A style edited through REST is drawn with its new colors by the wms service."""
    point = point_layer("test_propagation_style")
    point.use_style("colored", point_sld(RED, COVERING_SIZE))
    assert wait_until(lambda: point.map_color() == RGB[RED])

    point.update_style("colored", point_sld(BLUE, COVERING_SIZE))

    assert wait_until(
        lambda: point.map_color() == RGB[BLUE]
    ), "GetMap draws the old style"


@pytest.mark.db
def test_group_nesting_follows_rest_changes(point_layer):
    """The nesting of layer groups in the WMS capabilities follows changes made through REST."""
    point = point_layer("test_propagation_groups")
    workspace = point.workspace
    _, code = point.geoserver.create_layer_group(
        "inner", workspace, layers=[point.name]
    )
    assert code == 201
    outer = f"""<layerGroup><name>outer</name><mode>NAMED</mode>
      <workspace><name>{workspace}</name></workspace>
      <publishables><published type="layerGroup"><name>{workspace}:inner</name></published></publishables>
      <styles><style/></styles></layerGroup>"""
    response = point.rest.post(
        f"/rest/workspaces/{workspace}/layergroups",
        data=outer,
        headers=XML_CONTENT_TYPE,
    )
    assert response.status_code == 201

    def children_of_outer() -> list[str] | None:
        for name, children in wms_layers(point.wms_capabilities()):
            if local_name(name) == "outer":
                return [local_name(child) for child in children]
        return None

    assert wait_until(
        lambda: children_of_outer() == ["inner"]
    ), "outer does not list inner"

    replaced = f"""<layerGroup><name>outer</name><mode>NAMED</mode>
      <publishables><published type="layer"><name>{workspace}:{point.name}</name></published></publishables>
      <styles><style/></styles></layerGroup>"""
    response = point.rest.put(
        f"/rest/workspaces/{workspace}/layergroups/outer",
        data=replaced,
        headers=XML_CONTENT_TYPE,
    )
    assert response.status_code == 200

    assert wait_until(
        lambda: children_of_outer() == [point.name]
    ), "outer still lists inner"


def test_workspace_rename_spares_similar_names(geoserver, request):
    """Renaming a workspace leaves the files of a workspace with a similar name in place.

    The resource store matched the files below workspaces/ws_1 with a pattern in
    which the underscore matched any character, and renaming ws_1 also moved the
    files of ws21.
    """
    base = "test_propagation_ws"
    renamed_source, lookalike, target = f"{base}_1", f"{base}21", f"{base}_renamed"
    for workspace in (renamed_source, lookalike):
        _, code = geoserver.create_workspace(workspace)
        assert code == 201
        request.addfinalizer(
            lambda workspace=workspace: geoserver.delete_workspace(workspace)
        )
        _, code = geoserver.create_style_from_string("s", point_sld(RED, 8), workspace)
        assert code in (200, 201)
    request.addfinalizer(lambda: geoserver.delete_workspace(target))
    rest = geoserver.rest_service.rest_client
    lookalike_file = f"/rest/resource/workspaces/{lookalike}/styles/s.sld"
    assert http_get(geoserver, lookalike_file).status_code == 200

    response = rest.put(
        f"/rest/workspaces/{renamed_source}", json={"workspace": {"name": target}}
    )
    assert response.status_code == 200

    assert wait_until(
        lambda: http_get(
            geoserver, f"/rest/resource/workspaces/{target}/styles/s.sld"
        ).status_code
        == 200
    ), "the renamed workspace has no style file"
    assert (
        http_get(geoserver, lookalike_file).status_code == 200
    ), "the lookalike workspace lost its style file"
    assert (
        http_get(geoserver, f"/rest/workspaces/{lookalike}/styles/s.sld").status_code
        == 200
    )


@pytest.mark.db
@pytest.mark.xfail(
    strict=False,
    reason="GeoServer Cloud lists the tile layers of all workspaces in a workspace WMTS; the gwc service loses the workspace of the request",
)
def test_workspace_wmts_lists_its_own_layers(point_layer):
    """The WMTS capabilities of a workspace list the tile layers of that workspace only."""
    first = point_layer("test_propagation_wmts1")
    second = point_layer("test_propagation_wmts2")
    first.wait_for_tile_layer()
    second.wait_for_tile_layer()
    capabilities = {"service": "WMTS", "version": "1.0.0", "request": "GetCapabilities"}

    def names(path: str) -> list[str]:
        return wmts_layer_names(http_get(first.geoserver, path, capabilities).content)

    assert wait_until(
        lambda: first.name in names(f"/{first.workspace}/gwc/service/wmts")
    )
    assert second.name not in names(f"/{first.workspace}/gwc/service/wmts")
    assert second.prefixed_name not in names(f"/{first.workspace}/gwc/service/wmts")
    assert first.prefixed_name in names("/gwc/service/wmts")
    assert second.prefixed_name in names("/gwc/service/wmts")


@pytest.mark.db
def test_same_layer_name_in_two_workspaces(point_layer):
    """Two layers of the same name in different workspaces are told apart by their prefix."""
    first = point_layer("test_propagation_name1", layer="roads")
    second = point_layer("test_propagation_name2", layer="roads")
    first.use_style("fill_red", point_sld(RED, COVERING_SIZE))
    second.use_style("fill_blue", point_sld(BLUE, COVERING_SIZE))

    def color_of(point: PointLayer) -> tuple[int, ...] | None:
        response = point.get_map(workspace=None, layers=point.prefixed_name)
        return first_pixel(response.content) if is_image(response) else None

    assert wait_until(lambda: color_of(first) == RGB[RED])
    assert wait_until(lambda: color_of(second) == RGB[BLUE])


@pytest.mark.db
def test_tile_layer_formats_follow_gwc_rest(point_layer):
    """Tile requests honor the formats set on the tile layer through the GWC REST API."""
    point = point_layer("test_propagation_formats")
    point.wait_for_tile_layer()
    assert wait_until(lambda: is_image(point.get_tile("image/png")))

    jpeg_only = f"""<GeoServerLayer><enabled>true</enabled><name>{point.prefixed_name}</name>
      <mimeFormats><string>image/jpeg</string></mimeFormats>
      <gridSubsets><gridSubset><gridSetName>EPSG:4326</gridSetName></gridSubset></gridSubsets>
      </GeoServerLayer>"""
    response = point.rest.put(
        f"/gwc/rest/layers/{point.prefixed_name}.xml",
        data=jpeg_only,
        headers=XML_CONTENT_TYPE,
    )
    assert response.status_code == 200

    assert wait_until(
        lambda: not is_image(point.get_tile("image/png"))
    ), "PNG tiles still served"
    assert wait_until(lambda: is_image(point.get_tile("image/jpeg"), "image/jpeg"))
