from typing import Any

from geoservercloud.models.abstractlayer import AbstractLayer
from geoservercloud.models.common import EntityModel


class WmsLayer(AbstractLayer):
    def __init__(
        self,
        # Mandatory fields
        name: str,
        native_name: str,
        workspace_name: str,
        store_name: str,
        # Nullable fields
        srs: str | None = None,
        namespace_name: str | None = None,
        title: dict[str, str] | str | None = None,
        abstract: dict[str, str] | str | None = None,
        keywords: list[str] | None = None,
        native_bounding_box: dict[str, Any] | None = None,
        lat_lon_bounding_box: dict[str, Any] | None = None,
        attributes: list[dict[str, Any]] | None = None,
        projection_policy: str | None = None,
        enabled: bool | None = None,
        epsg_code: int | None = None,
        description: str | None = None,
        native_crs: dict | None = None,
        forced_remote_style: str | None = None,
        preferred_format: str | None = None,
        metadata_bbox_respected: bool | None = None,
        service_configuration: bool | None = None,
    ):
        super().__init__(
            name=name,
            native_name=native_name,
            workspace_name=workspace_name,
            store_name=store_name,
            srs=srs,
            namespace_name=namespace_name,
            title=title,
            abstract=abstract,
            keywords=keywords,
            native_bounding_box=native_bounding_box,
            lat_lon_bounding_box=lat_lon_bounding_box,
            projection_policy=projection_policy,
            enabled=enabled,
            epsg_code=epsg_code,
            service_configuration=service_configuration,
        )
        self.description: str | None = description
        self.native_crs: dict | None = native_crs
        self.forced_remote_style: str | None = forced_remote_style
        self.preferred_format: str | None = preferred_format
        self.metadata_bbox_respected: bool | None = metadata_bbox_respected

    @classmethod
    def from_get_response_payload(cls, content: dict):
        wms_layer = content["wmsLayer"]
        workspace_name = wms_layer["store"]["name"].split(":")[0]
        store_name = wms_layer["store"]["name"].split(":")[1]
        return cls(
            name=wms_layer["name"],
            native_name=wms_layer["nativeName"],
            workspace_name=workspace_name,
            store_name=store_name,
            srs=wms_layer["srs"],
            namespace_name=wms_layer["namespace"]["name"],
            title=wms_layer.get("title"),
            abstract=wms_layer.get("abstract"),
            keywords=wms_layer.get("keywords", {}).get("string", []),
            native_bounding_box=wms_layer.get("nativeBoundingBox"),
            lat_lon_bounding_box=wms_layer.get("latLonBoundingBox"),
            projection_policy=wms_layer.get("projectionPolicy"),
            enabled=wms_layer.get("enabled"),
            description=wms_layer.get("description"),
            native_crs=wms_layer.get("nativeCRS"),
            forced_remote_style=wms_layer.get("forcedRemoteStyle"),
            preferred_format=wms_layer.get("preferredFormat"),
            metadata_bbox_respected=wms_layer.get("metadataBBoxRespected"),
            service_configuration=wms_layer.get("serviceConfiguration"),
        )

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = super().asdict()
        optional_items = {
            "description": self.description,
            "nativeCRS": self.native_crs,
            "forcedRemoteStyle": self.forced_remote_style,
            "preferredFormat": self.preferred_format,
            "metadataBBoxRespected": self.metadata_bbox_respected,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        content = self.asdict()
        if self.keywords is not None:
            content["keywords"] = {"string": self.keywords}
        return {"wmsLayer": content}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()
