from typing import Any

from geoservercloud.models.common import I18N, EntityModel, ReferencedObjectModel
from geoservercloud.utils import EPSG_BBOX


class AbstractLayer(EntityModel):
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
        keywords: str | list[str] | None = None,
        native_bounding_box: dict[str, Any] | None = None,
        lat_lon_bounding_box: dict[str, Any] | None = None,
        projection_policy: str | None = None,
        enabled: bool | None = None,
        epsg_code: int | None = None,
        service_configuration: bool | None = None,
    ):

        self.name: str = name
        self.native_name: str = native_name
        self.srs: str | None = srs
        self.workspace_name: str = workspace_name
        self.store = ReferencedObjectModel(f"{workspace_name}:{store_name}")
        self.namespace: ReferencedObjectModel | None = (
            ReferencedObjectModel(namespace_name) if namespace_name else None
        )
        self.title: I18N | None = (
            I18N(("title", "internationalTitle"), title) if title else None
        )
        self.abstract: I18N | None = (
            I18N(("abstract", "internationalAbstract"), abstract) if abstract else None
        )
        self.keywords: list[str] | None = (
            keywords if not isinstance(keywords, str) else [keywords]
        )
        self.native_bounding_box: dict[str, Any] | None = native_bounding_box
        self.lat_lon_bounding_box: dict[str, Any] | None = lat_lon_bounding_box
        self.projection_policy: str | None = projection_policy
        self.enabled: bool | None = enabled
        self.epsg_code: int | None = epsg_code
        self.service_configuration: bool | None = service_configuration

    @property
    def store_name(self) -> str:
        return self.store.name.split(":")[1]

    @property
    def namespace_name(self) -> str | None:
        return self.namespace.name if self.namespace else None

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {
            "name": self.name,
            "nativeName": self.native_name,
            "store": self.store.asdict(),
        }
        if self.namespace is not None:
            content["namespace"] = self.namespace.asdict()
        if self.title:
            content.update(self.title.asdict())
        if self.abstract:
            content.update(self.abstract.asdict())
        if self.native_bounding_box:
            content["nativeBoundingBox"] = self.native_bounding_box
        elif self.epsg_code:
            content["nativeBoundingBox"] = EPSG_BBOX[self.epsg_code][
                "nativeBoundingBox"
            ]
        if self.lat_lon_bounding_box:
            content["latLonBoundingBox"] = self.lat_lon_bounding_box
        elif self.epsg_code:
            content["latLonBoundingBox"] = EPSG_BBOX[self.epsg_code][
                "latLonBoundingBox"
            ]
        optional_items = {
            "srs": self.srs,
            "keywords": self.keywords,
            "projectionPolicy": self.projection_policy,
            "enabled": self.enabled,
            "serviceConfiguration": self.service_configuration,
        }
        return EntityModel.add_items_to_dict(content, optional_items)
