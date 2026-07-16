from typing import Any

from geoservercloud.models.common import BaseModel, EntityModel


class GridSubsetExtent(BaseModel):
    def __init__(self, coords: list[float]):
        self.coords: list[float] = coords

    @classmethod
    def from_get_response_payload(cls, content: dict):
        return cls(coords=content["coords"])

    def asdict(self) -> dict[str, Any]:
        return {"coords": self.coords}


class GridSubset(BaseModel):
    def __init__(
        self,
        grid_set_name: str,
        extent: GridSubsetExtent | None = None,
    ):
        self.grid_set_name: str = grid_set_name
        self.extent: GridSubsetExtent | None = extent

    @classmethod
    def from_get_response_payload(cls, content: dict):
        extent = content.get("extent")
        return cls(
            grid_set_name=content["gridSetName"],
            extent=(
                GridSubsetExtent.from_get_response_payload(extent) if extent else None
            ),
        )

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {"gridSetName": self.grid_set_name}
        if self.extent is not None:
            content["extent"] = self.extent.asdict()
        return content


class ParameterFilter(BaseModel):
    def __init__(self, key: str, default_value: str = ""):
        self.key: str = key
        self.default_value: str = default_value

    @classmethod
    def from_get_response_payload(cls, content: dict):
        return cls(key=content["key"], default_value=content.get("defaultValue", ""))

    def asdict(self) -> dict[str, Any]:
        return {"key": self.key, "defaultValue": self.default_value}


class GwcLayer(EntityModel):
    def __init__(
        self,
        # Mandatory fields
        workspace_name: str,
        layer_name: str,
        # Nullable fields
        id: str | None = None,
        enabled: bool | None = None,
        grid_subsets: list[GridSubset] | None = None,
        mime_formats: list[str] | None = None,
        parameter_filters: list[ParameterFilter] | None = None,
        meta_width_height: list[int] | None = None,
        gutter: int | None = None,
        expire_cache: int | None = None,
        expire_clients: int | None = None,
        cache_warning_skips: list[Any] | None = None,
    ):
        self.workspace_name: str = workspace_name
        self.layer_name: str = layer_name
        self.id: str | None = id
        self.enabled: bool | None = enabled
        self.grid_subsets: list[GridSubset] | None = grid_subsets
        self.mime_formats: list[str] | None = mime_formats
        self.parameter_filters: list[ParameterFilter] | None = parameter_filters
        self.meta_width_height: list[int] | None = meta_width_height
        self.gutter: int | None = gutter
        self.expire_cache: int | None = expire_cache
        self.expire_clients: int | None = expire_clients
        self.cache_warning_skips: list[Any] | None = cache_warning_skips

    @property
    def name(self) -> str:
        return f"{self.workspace_name}:{self.layer_name}"

    @classmethod
    def from_get_response_payload(cls, content: dict):
        gwc_layer = content["GeoServerLayer"]
        workspace_name, layer_name = gwc_layer["name"].split(":", 1)
        grid_subsets = gwc_layer.get("gridSubsets")
        if isinstance(grid_subsets, dict):
            grid_subsets = grid_subsets.get("gridSubset", [])
        parameter_filters = gwc_layer.get("parameterFilters")
        meta_width_height = gwc_layer.get("metaWidthHeight")
        if isinstance(meta_width_height, dict):
            meta_width_height = meta_width_height.get("int", [])
        return cls(
            workspace_name=workspace_name,
            layer_name=layer_name,
            id=gwc_layer.get("id"),
            enabled=gwc_layer.get("enabled"),
            grid_subsets=(
                [GridSubset.from_get_response_payload(item) for item in grid_subsets]
                if grid_subsets is not None
                else None
            ),
            mime_formats=gwc_layer.get("mimeFormats"),
            parameter_filters=(
                [
                    ParameterFilter.from_get_response_payload(item)
                    for item in parameter_filters
                ]
                if parameter_filters is not None
                else None
            ),
            meta_width_height=meta_width_height,
            gutter=gwc_layer.get("gutter"),
            expire_cache=gwc_layer.get("expireCache"),
            expire_clients=gwc_layer.get("expireClients"),
            cache_warning_skips=gwc_layer.get("cacheWarningSkips"),
        )

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {"name": self.name}
        optional_items: dict[str, Any] = {
            "id": self.id,
            "enabled": self.enabled,
            "gridSubsets": (
                {"gridSubset": [item.asdict() for item in self.grid_subsets]}
                if self.grid_subsets is not None
                else None
            ),
            "mimeFormats": self.mime_formats,
            "parameterFilters": (
                [item.asdict() for item in self.parameter_filters]
                if self.parameter_filters is not None
                else None
            ),
            "metaWidthHeight": (
                {"int": self.meta_width_height}
                if self.meta_width_height is not None
                else None
            ),
            "gutter": self.gutter,
            "expireCache": self.expire_cache,
            "expireClients": self.expire_clients,
            "cacheWarningSkips": self.cache_warning_skips,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        return {"GeoServerLayer": self.asdict()}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()
