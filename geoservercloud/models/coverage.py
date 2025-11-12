from geoservercloud.models.abstractlayer import AbstractLayer
from geoservercloud.models.common import EntityModel, KeyDollarListDict


class Coverage(AbstractLayer):
    """A GeoServer Coverage (raster layer)."""

    def __init__(
        self,
        name: str,
        title: str,
        native_name: str,
        workspace_name: str,
        store_name: str,
        # Nullable fields
        srs: str | None = None,
        namespace_name: str | None = None,
        enabled: bool = True,
        description: str | None = None,
        keywords: list[str] | None = None,
        native_bounding_box: dict[str, object] | None = None,
        lat_lon_bounding_box: dict[str, object] | None = None,
        projection_policy: str | None = None,
        epsg_code: int | None = None,
        service_configuration: bool | None = None,
        native_crs: str | None = None,
        metadata: dict[str, object] | None = None,
        simple_conversion_format: str | None = None,
        native_format: str | None = None,
        grid: dict | None = None,
        supported_formats: dict | None = None,
        interpolation_methods: dict | None = None,
        default_interpolation_method: str | None = None,
        dimensions: dict | None = None,
        requestSRS: dict | None = None,
        parameters: dict | None = None,
        native_coverage_name: str | None = None,
    ):
        super().__init__(
            name=name,
            native_name=native_name,
            workspace_name=workspace_name,
            store_name=store_name,
            srs=srs,
            namespace_name=namespace_name,
            title=title,
            keywords=keywords,
            native_bounding_box=native_bounding_box,
            lat_lon_bounding_box=lat_lon_bounding_box,
            projection_policy=projection_policy,
            enabled=enabled,
            epsg_code=epsg_code,
            service_configuration=service_configuration,
        )
        self.description: str | None = description
        self.native_crs: str | None = native_crs
        self.metadata: KeyDollarListDict | None = None
        if metadata is not None:
            self.metadata = KeyDollarListDict(input_dict=metadata)
        self.simple_conversion_format: str | None = simple_conversion_format
        self.native_format: str | None = native_format
        self.grid: dict | None = grid
        self.supported_formats: dict | None = supported_formats
        self.interpolation_methods: dict | None = interpolation_methods
        self.default_interpolation_method: str | None = default_interpolation_method
        self.dimensions: dict | None = dimensions
        self.requestSRS: dict | None = requestSRS
        self.parameters: dict | None = parameters
        self.native_coverage_name: str | None = native_coverage_name

    def asdict(self) -> dict[str, object]:
        content: dict[str, object] = super().asdict()
        optional_items = {
            "description": self.description,
            "nativeCRS": self.native_crs,
            "simpleConversionFormat": self.simple_conversion_format,
            "nativeFormat": self.native_format,
            "grid": self.grid,
            "supportedFormats": self.supported_formats,
            "interpolationMethods": self.interpolation_methods,
            "defaultInterpolationMethod": self.default_interpolation_method,
            "dimensions": self.dimensions,
            "requestSRS": self.requestSRS,
            "parameters": self.parameters,
            "nativeCoverageName": self.native_coverage_name,
        }
        if self.metadata:
            optional_items["metadata"] = {"entry": dict(self.metadata)}
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, object]:
        return {"coverage": self.asdict()}

    def put_payload(self) -> dict[str, object]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        coverage = content["coverage"]
        metadata: dict[str, object] | None = None
        if coverage.get("metadata"):
            metadata = {"entry": dict(coverage.get("metadata", {}).get("entry", {}))}
        return cls(
            name=coverage["name"],
            workspace_name=coverage["namespace"]["name"],
            store_name=coverage["store"]["name"].split(":")[1],
            srs=coverage.get("srs", None),
            namespace_name=coverage["namespace"]["name"],
            title=coverage.get("title"),
            native_name=coverage.get("nativeName"),
            enabled=coverage.get("enabled", True),
            description=coverage.get("description", None),
            native_crs=coverage.get("nativeCRS", None),
            metadata=metadata,
            simple_conversion_format=coverage.get("simpleConversionFormat", None),
            native_format=coverage.get("nativeFormat", None),
            grid=coverage.get("grid", None),
            supported_formats=coverage.get("supportedFormats", None),
            interpolation_methods=coverage.get("interpolationMethods", None),
            default_interpolation_method=coverage.get(
                "defaultInterpolationMethod", None
            ),
            dimensions=coverage.get("dimensions", None),
            requestSRS=coverage.get("requestSRS", None),
            parameters=coverage.get("parameters", None),
            native_coverage_name=coverage.get("nativeCoverageName", None),
        )
