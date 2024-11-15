from typing import Any

from geoservercloud.models.common import EntityModel, ReferencedObjectModel


class WmsSettings(EntityModel):
    def __init__(
        self,
        workspace_name: str | None = None,
        name: str | None = None,
        enabled: bool | None = None,
        default_locale: str | None = None,
        auto_escape_template_values: bool | None = None,
        bbox_for_each_crs: bool | None = None,
        cache_configuration: dict[str, bool | int] | None = None,
        cite_compliant: bool | None = None,
        default_group_style_enabled: bool | None = None,
        dynamic_styling_disabled: bool | None = None,
        features_reprojection_disabled: bool | None = None,
        get_feature_info_mime_type_checking_enabled: bool | None = None,
        get_map_mime_type_checking_enabled: bool | None = None,
        interpolation: str | None = None,
        max_buffer: int | None = None,
        max_rendering_errors: int | None = None,
        max_rendering_time: int | None = None,
        max_request_memory: int | None = None,
        max_requested_dimension_values: int | None = None,
        remote_style_max_request_time: int | None = None,
        remote_style_timeout: int | None = None,
        schema_base_url: str | None = None,
        transform_feature_info_disabled: bool | None = None,
        verbose: bool | None = None,
        versions: dict[str, list[dict[str, str]]] | None = None,
        watermark: dict[str, bool | int | str] | None = None,
    ) -> None:
        self.workspace: ReferencedObjectModel | None = (
            ReferencedObjectModel(workspace_name) if workspace_name else None
        )
        self.name: str | None = name
        self.enabled: bool | None = enabled
        self.default_locale: str | None = default_locale
        self.auto_escape_template_values: bool | None = auto_escape_template_values
        self.bbox_for_each_crs: bool | None = bbox_for_each_crs
        self.cache_configuration: dict[str, bool | int] | None = cache_configuration
        self.cite_compliant: bool | None = cite_compliant
        self.default_group_style_enabled: bool | None = default_group_style_enabled
        self.dynamic_styling_disabled: bool | None = dynamic_styling_disabled
        self.features_reprojection_disabled: bool | None = (
            features_reprojection_disabled
        )
        self.get_feature_info_mime_type_checking_enabled: bool | None = (
            get_feature_info_mime_type_checking_enabled
        )
        self.get_map_mime_type_checking_enabled: bool | None = (
            get_map_mime_type_checking_enabled
        )
        self.interpolation: str | None = interpolation
        self.max_buffer: int | None = max_buffer
        self.max_rendering_errors: int | None = max_rendering_errors
        self.max_rendering_time: int | None = max_rendering_time
        self.max_request_memory: int | None = max_request_memory
        self.max_requested_dimension_values: int | None = max_requested_dimension_values
        self.remote_style_max_request_time: int | None = remote_style_max_request_time
        self.remote_style_timeout: int | None = remote_style_timeout
        self.schema_base_url: str | None = schema_base_url
        self.transform_feature_info_disabled: bool | None = (
            transform_feature_info_disabled
        )
        self.verbose: bool | None = verbose
        self.versions: dict[str, list[dict[str, str]]] | None = versions
        self.watermark: dict[str, bool | int | str] | None = watermark

    @property
    def workspace_name(self) -> str | None:
        return self.workspace.name if self.workspace else None

    def asdict(self) -> dict[str, str]:
        return EntityModel.add_items_to_dict(
            {},
            {
                "workspace": self.workspace_name,
                "name": self.name,
                "enabled": self.enabled,
                "defaultLocale": self.default_locale,
                "autoEscapeTemplateValues": self.auto_escape_template_values,
                "bboxForEachCRS": self.bbox_for_each_crs,
                "cacheConfiguration": self.cache_configuration,
                "citeCompliant": self.cite_compliant,
                "defaultGroupStyleEnabled": self.default_group_style_enabled,
                "dynamicStylingDisabled": self.dynamic_styling_disabled,
                "featuresReprojectionDisabled": self.features_reprojection_disabled,
                "getFeatureInfoMimeTypeCheckingEnabled": self.get_feature_info_mime_type_checking_enabled,
                "getMapMimeTypeCheckingEnabled": self.get_map_mime_type_checking_enabled,
                "interpolation": self.interpolation,
                "maxBuffer": self.max_buffer,
                "maxRenderingErrors": self.max_rendering_errors,
                "maxRenderingTime": self.max_rendering_time,
                "maxRequestMemory": self.max_request_memory,
                "maxRequestedDimensionValues": self.max_requested_dimension_values,
                "remoteStyleMaxRequestTime": self.remote_style_max_request_time,
                "remoteStyleTimeout": self.remote_style_timeout,
                "schemaBaseURL": self.schema_base_url,
                "transformFeatureInfoDisabled": self.transform_feature_info_disabled,
                "verbose": self.verbose,
                "versions": self.versions,
                "watermark": self.watermark,
            },
        )

    def post_payload(self) -> dict[str, Any]:
        content: dict[str, Any] = self.asdict()
        if self.workspace:
            content["workspace"] = self.workspace.asdict()
        return {"wms": content}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict[str, Any]):
        wms_settings = content["wms"]
        return cls(
            workspace_name=wms_settings.get("workspace", {}).get("name"),
            name=wms_settings.get("name"),
            enabled=wms_settings.get("enabled"),
            default_locale=wms_settings.get("defaultLocale"),
            auto_escape_template_values=wms_settings.get("autoEscapeTemplateValues"),
            bbox_for_each_crs=wms_settings.get("bboxForEachCRS"),
            cache_configuration=wms_settings.get("cacheConfiguration"),
            cite_compliant=wms_settings.get("citeCompliant"),
            default_group_style_enabled=wms_settings.get("defaultGroupStyleEnabled"),
            dynamic_styling_disabled=wms_settings.get("dynamicStylingDisabled"),
            features_reprojection_disabled=wms_settings.get(
                "featuresReprojectionDisabled"
            ),
            get_feature_info_mime_type_checking_enabled=wms_settings.get(
                "getFeatureInfoMimeTypeCheckingEnabled"
            ),
            get_map_mime_type_checking_enabled=wms_settings.get(
                "getMapMimeTypeCheckingEnabled"
            ),
            interpolation=wms_settings.get("interpolation"),
            max_buffer=wms_settings.get("maxBuffer"),
            max_rendering_errors=wms_settings.get("maxRenderingErrors"),
            max_rendering_time=wms_settings.get("maxRenderingTime"),
            max_request_memory=wms_settings.get("maxRequestMemory"),
            max_requested_dimension_values=wms_settings.get(
                "maxRequestedDimensionValues"
            ),
            remote_style_max_request_time=wms_settings.get("remoteStyleMaxRequestTime"),
            remote_style_timeout=wms_settings.get("remoteStyleTimeout"),
            schema_base_url=wms_settings.get("schemaBaseURL"),
            transform_feature_info_disabled=wms_settings.get(
                "transformFeatureInfoDisabled"
            ),
            verbose=wms_settings.get("verbose"),
            versions=wms_settings.get("versions"),
            watermark=wms_settings.get("watermark"),
        )
