from pathlib import Path
from typing import Any

from owslib.map.wms130 import WebMapService_1_3_0
from owslib.util import ResponseWrapper
from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud import utils
from geoservercloud.models.common import TimeDimensionInfo
from geoservercloud.models.coverage import Coverage
from geoservercloud.models.coveragestore import CoverageStore
from geoservercloud.models.datastore import DataStore
from geoservercloud.models.featuretype import FeatureType
from geoservercloud.models.layer import Layer
from geoservercloud.models.layergroup import LayerGroup
from geoservercloud.models.style import Style
from geoservercloud.models.wmslayer import WmsLayer
from geoservercloud.models.wmssettings import WmsSettings
from geoservercloud.models.wmsstore import WmsStore
from geoservercloud.models.workspace import Workspace
from geoservercloud.services import OwsService, RestService
from geoservercloud.templates import Templates


class GeoServerCloud:
    """
    Facade class allowing CRUD operations on GeoServer resources

    Attributes
    ----------
    url : str
        base GeoServer URL
    user : str
        GeoServer username
    password : str
        GeoServer password
    """

    def __init__(
        self,
        url: str = "http://localhost:9090/geoserver/cloud",
        user: str = "admin",
        password: str = "geoserver",  # nosec
        verifytls: bool = True,
    ) -> None:

        self.url: str = url.strip("/")
        self.user: str = user
        self.password: str = password
        self.auth: tuple[str, str] = (user, password)
        self.rest_service: RestService = RestService(self.url, self.auth, verifytls)
        self.ows_service: OwsService = OwsService(self.url, self.auth, verifytls)
        self.wms: WebMapService_1_3_0 | None = None
        self.wmts: WebMapTileService | None = None
        self.default_workspace: str | None = None
        self.default_datastore: str | None = None

    def get_version(self) -> tuple[dict[str, dict[str, list]] | str, int]:
        """
        Get GeoServer version information

        Returns
        -------
        tuple
            A tuple containing:
                - content (dict[str, dict[str, list]] or str): The version information as a dictionary if the
                  request is successful ({'about': {'resource': [...]}}) or an error message as a string if
                  the request fails.
                - status (int): The HTTP status code of the response.
        """
        return self.rest_service.get_version()

    def create_wms(self, workspace: str | None = None) -> None:
        if workspace:
            self.wms = self.ows_service.create_wms(workspace)
        elif self.default_workspace:
            self.wms = self.ows_service.create_wms(self.default_workspace)
        else:
            self.wms = self.ows_service.create_wms()

    def create_wmts(self, workspace_name: str | None = None) -> None:
        if workspace_name:
            self.wmts = self.ows_service.create_wmts(workspace_name)
        elif self.default_workspace:
            self.wmts = self.ows_service.create_wmts(self.default_workspace)
        else:
            self.wmts = self.ows_service.create_wmts()

    def cleanup(self):
        """
        Cleanup internal state
        """
        self.wms = None
        self.wmts = None
        self.default_workspace = None
        self.default_datastore = None

    def get_workspaces(self) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all GeoServer workspaces
        """
        workspaces, status_code = self.rest_service.get_workspaces()
        if isinstance(workspaces, str):
            return workspaces, status_code
        return workspaces.aslist(), status_code

    def get_workspace(self, workspace_name: str) -> tuple[dict[str, str] | str, int]:
        """
        Get a workspace by name
        """
        workspace, status_code = self.rest_service.get_workspace(workspace_name)
        if isinstance(workspace, str):
            return workspace, status_code
        return workspace.asdict(), status_code

    def create_workspace(
        self,
        workspace_name: str,
        isolated: bool = False,
        set_default_workspace: bool = False,
    ) -> tuple[str, int]:
        """
        Create a workspace in GeoServer, if it does not already exist.
        It if exists, update it
        """
        workspace = Workspace(workspace_name, isolated)
        content, status_code = self.rest_service.create_workspace(workspace)
        if set_default_workspace:
            self.default_workspace = workspace_name
        return content, status_code

    def delete_workspace(self, workspace_name: str) -> tuple[str, int]:
        """
        Delete a GeoServer workspace (recursively)
        """
        content, status_code = self.rest_service.delete_workspace(
            Workspace(workspace_name)
        )
        if self.default_workspace == workspace_name:
            self.default_workspace = None
            self.wms = None
            self.wmts = None
        return content, status_code

    def recreate_workspace(
        self,
        workspace_name: str,
        isolated: bool = False,
        set_default_workspace: bool = False,
    ) -> tuple[str, int]:
        """
        Create a workspace in GeoServer, and first delete it if it already exists.
        """
        self.delete_workspace(workspace_name)
        return self.create_workspace(
            workspace_name,
            isolated=isolated,
            set_default_workspace=set_default_workspace,
        )

    def get_workspace_wms_settings(
        self, workspace_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get the WMS settings for a given workspace
        """
        wms_settings, status_code = self.rest_service.get_workspace_wms_settings(
            workspace_name
        )
        if isinstance(wms_settings, str):
            return wms_settings, status_code
        return wms_settings.asdict(), status_code

    def publish_workspace(
        self,
        workspace_name: str,
        versions: list[str] = ["1.1.1", "1.3.0"],
        cite_compliant: bool = False,
        schema_base_url: str = "http://schemas.opengis.net",
        verbose: bool = False,
        bbox_for_each_crs: bool = False,
        watermark: dict = {
            "enabled": False,
            "position": "BOT_RIGHT",
            "transparency": 100,
        },
        interpolation: str = "Nearest",
        get_feature_info_mime_type_checking_enabled: bool = False,
        get_map_mime_type_checking_enabled: bool = False,
        dynamic_styling_disabled: bool = False,
        features_reprojection_disabled: bool = False,
        max_buffer: int = 0,
        max_request_memory: int = 0,
        max_rendering_time: int = 0,
        max_rendering_errors: int = 0,
        max_requested_dimension_values: int = 100,
        cache_configuration: dict = {
            "enabled": False,
            "maxEntries": 1000,
            "maxEntrySize": 51200,
        },
        remote_style_max_request_time: int = 60000,
        remote_style_timeout: int = 30000,
        default_group_style_enabled: bool = True,
        transform_feature_info_disabled: bool = False,
        auto_escape_template_values: bool = False,
    ) -> tuple[str, int]:
        """
        Publish the WMS service for a given workspace
        """
        wms_settings = WmsSettings(
            workspace_name=workspace_name,
            name="WMS",
            enabled=True,
            versions={
                "org.geotools.util.Version": [
                    {"version": version} for version in versions
                ]
            },
            cite_compliant=cite_compliant,
            schema_base_url=schema_base_url,
            verbose=verbose,
            bbox_for_each_crs=bbox_for_each_crs,
            watermark=watermark,
            interpolation=interpolation,
            get_feature_info_mime_type_checking_enabled=get_feature_info_mime_type_checking_enabled,
            get_map_mime_type_checking_enabled=get_map_mime_type_checking_enabled,
            dynamic_styling_disabled=dynamic_styling_disabled,
            features_reprojection_disabled=features_reprojection_disabled,
            max_buffer=max_buffer,
            max_request_memory=max_request_memory,
            max_rendering_time=max_rendering_time,
            max_rendering_errors=max_rendering_errors,
            max_requested_dimension_values=max_requested_dimension_values,
            cache_configuration=cache_configuration,
            remote_style_max_request_time=remote_style_max_request_time,
            remote_style_timeout=remote_style_timeout,
            default_group_style_enabled=default_group_style_enabled,
            transform_feature_info_disabled=transform_feature_info_disabled,
            auto_escape_template_values=auto_escape_template_values,
        )
        return self.rest_service.put_workspace_wms_settings(
            workspace_name, wms_settings
        )

    def set_default_locale_for_service(
        self, workspace_name: str, locale: str | None
    ) -> tuple[str, int]:
        """
        Set a default language for localized WMS requests
        """
        wms_settings = WmsSettings(default_locale=locale)
        return self.rest_service.put_workspace_wms_settings(
            workspace_name, wms_settings
        )

    def unset_default_locale_for_service(self, workspace_name) -> tuple[str, int]:
        """
        Remove the default language for localized WMS requests
        """
        return self.set_default_locale_for_service(workspace_name, None)

    def get_datastores(
        self, workspace_name: str
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all datastores for a given workspace
        """
        datastores, status_code = self.rest_service.get_datastores(workspace_name)
        if isinstance(datastores, str):
            return datastores, status_code
        return datastores.aslist(), status_code

    def get_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a datastore by workspace and name
        """
        datastore, status_code = self.rest_service.get_datastore(
            workspace_name, datastore_name
        )
        if isinstance(datastore, str):
            return datastore, status_code
        return datastore.asdict(), status_code

    def get_pg_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a datastore by workspace and name
        """
        return self.get_datastore(workspace_name, datastore_name)

    def create_datastore(
        self,
        workspace_name: str,
        datastore_name: str,
        datastore_type: str,
        connection_parameters: dict[str, Any],
        description: str | None = None,
        enabled: bool = True,
        set_default_datastore: bool = False,
    ) -> tuple[str, int]:
        """
        Create a generic datastore of any type in GeoServer, or update if it already exists. This method
        accepts flexible connection parameters, allowing to create any type of datastore.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name for the datastore
        :type datastore_name: str
        :param datastore_type: Type of datastore (e.g., "PostGIS", "Shapefile", "Directory of spatial files (shapefiles)")
        :type datastore_type: str
        :param connection_parameters: Dict of connection parameters specific to the datastore type
        :type connection_parameters: dict
        :param description: Optional description
        :type description: str, optional
        :param enabled: Whether the datastore should be enabled (default: True)
        :type enabled: bool, optional
        :param set_default_datastore: Whether to set as default datastore (default: False)
        :type set_default_datastore: bool, optional

        :return: Tuple of (datastore_name, status_code)
        :rtype: tuple

        :Example:

        >>> create_datastore(
        ...     workspace_name="myworkspace",
        ...     datastore_name="my_store",
        ...     datastore_type="PostGIS",
        ...     connection_parameters={
        ...         "dbtype": "postgis",
        ...         "host": "localhost",
        ...         "port": 5432,
        ...         "database": "mydb",
        ...         "user": "user",
        ...         "passwd": "password",
        ...         "schema": "public",
        ...         "Expose primary keys": "true",
        ...     }
        ... )
        """
        datastore = DataStore(
            workspace_name,
            datastore_name,
            connection_parameters=connection_parameters,
            type=datastore_type,
            description=description,
            enabled=enabled,
        )
        content, status_code = self.rest_service.create_datastore(
            workspace_name, datastore
        )

        if set_default_datastore:
            self.default_datastore = datastore_name

        return content, status_code

    def create_pg_datastore(
        self,
        workspace_name: str,
        datastore_name: str,
        pg_host: str,
        pg_port: int,
        pg_db: str,
        pg_user: str,
        pg_password: str,
        pg_schema: str = "public",
        description: str | None = None,
        set_default_datastore: bool = False,
    ) -> tuple[str, int]:
        """
        Create a PostGIS datastore from the DB connection parameters, or update it if it already exist.
        """
        datastore = DataStore(
            workspace_name,
            datastore_name,
            connection_parameters={
                "dbtype": "postgis",
                "host": pg_host,
                "port": pg_port,
                "database": pg_db,
                "user": pg_user,
                "passwd": pg_password,
                "schema": pg_schema,
                "namespace": f"http://{workspace_name}",
                "Expose primary keys": "true",
            },
            type="PostGIS",
            description=description,
        )
        content, status_code = self.rest_service.create_datastore(
            workspace_name, datastore
        )

        if set_default_datastore:
            self.default_datastore = datastore_name

        return content, status_code

    def create_jndi_datastore(
        self,
        workspace_name: str,
        datastore_name: str,
        jndi_reference: str,
        pg_schema: str = "public",
        description: str | None = None,
        set_default_datastore: bool = False,
    ) -> tuple[str, int]:
        """
        Create a PostGIS datastore from JNDI resource, or update it if it already exist.
        """
        datastore = DataStore(
            workspace_name,
            datastore_name,
            connection_parameters={
                "dbtype": "postgis",
                "jndiReferenceName": jndi_reference,
                "schema": pg_schema,
                "namespace": f"http://{workspace_name}",
                "Expose primary keys": "true",
            },
            type="PostGIS (JNDI)",
            description=description,
        )
        content, code = self.rest_service.create_datastore(workspace_name, datastore)

        if set_default_datastore:
            self.default_datastore = datastore_name

        return content, code

    def create_pmtiles_datastore(
        self,
        workspace_name: str,
        datastore_name: str,
        pmtiles_url: str,
        description: str | None = None,
        range_reader_provider: str = "file",
        caching_enabled: bool = True,
        caching_block_aligned: bool = True,
        http_timeout_millis: int = 5000,
        http_trust_all_certificates: bool = False,
        s3_use_default_credentials_provider: bool = False,
        s3_force_path_style: bool = True,
        gcs_default_credentials_chain: bool = False,
    ) -> tuple[str, int]:
        """
        Create a PMTiles datastore, or update it if it already exists.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name for the PMTiles datastore
        :type datastore_name: str
        :param pmtiles_url: URL or path to the PMTiles file
        :type pmtiles_url: str
        :param description: Optional description for the datastore
        :type description: str, optional
        :param range_reader_provider: Range reader provider type (default: "file")
        :type range_reader_provider: str, optional
        :param caching_enabled: Enable caching for range reader (default: True)
        :type caching_enabled: bool, optional
        :param caching_block_aligned: Enable block-aligned caching (default: True)
        :type caching_block_aligned: bool, optional
        :param http_timeout_millis: HTTP timeout in milliseconds (default: 5000)
        :type http_timeout_millis: int, optional
        :param http_trust_all_certificates: Trust all SSL certificates for HTTP (default: False)
        :type http_trust_all_certificates: bool, optional
        :param s3_use_default_credentials_provider: Use default AWS credentials provider for S3 (default: False)
        :type s3_use_default_credentials_provider: bool, optional
        :param s3_force_path_style: Force path-style access for S3 (default: True)
        :type s3_force_path_style: bool, optional
        :param gcs_default_credentials_chain: Use default credentials chain for Google Cloud Storage (default: False)
        :type gcs_default_credentials_chain: bool, optional

        :return: Tuple of (datastore_name, status_code)
        :rtype: tuple

        :Example:

        >>> create_pmtiles_datastore(
        ...     workspace_name="pmtiles_workspace",
        ...     datastore_name="pmtiles_store",
        ...     pmtiles_url="file:///mnt/pmtiles/mypmtilesfile.pmtiles",
        ...     description="My PMTiles datastore",
        ...     range_reader_provider="file",
        ... )
        """

        datastore = DataStore(
            workspace_name,
            datastore_name,
            connection_parameters={
                "pmtiles": pmtiles_url,
                "namespace": f"http://{workspace_name}",
                "io.tileverse.rangereader.provider": range_reader_provider,
                "io.tileverse.rangereader.caching.enabled": str(
                    caching_enabled
                ).lower(),
                "io.tileverse.rangereader.caching.blockaligned": str(
                    caching_block_aligned
                ).lower(),
                "io.tileverse.rangereader.http.timeout-millis": str(
                    http_timeout_millis
                ),
                "io.tileverse.rangereader.http.trust-all-certificates": str(
                    http_trust_all_certificates
                ).lower(),
                "io.tileverse.rangereader.s3.use-default-credentials-provider": str(
                    s3_use_default_credentials_provider
                ).lower(),
                "io.tileverse.rangereader.s3.force-path-style": str(
                    s3_force_path_style
                ).lower(),
                "io.tileverse.rangereader.gcs.default-credentials-chain": str(
                    gcs_default_credentials_chain
                ).lower(),
            },
            type="PMTiles",
            description=description,
        )
        return self.rest_service.create_datastore(workspace_name, datastore)

    def get_wms_store(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a WMS by workspace and name
        """
        wms_store, status_code = self.rest_service.get_wms_store(
            workspace_name, datastore_name
        )
        if isinstance(wms_store, str):
            return wms_store, status_code
        return wms_store.asdict(), status_code

    def create_wms_store(
        self,
        workspace_name: str,
        wms_store_name: str,
        capabilities_url: str,
    ) -> tuple[str, int]:
        """
        Create a cascaded WMS store, or update it if it already exist.
        """
        wms_store = WmsStore(
            workspace_name,
            wms_store_name,
            capabilities_url,
        )
        return self.rest_service.create_wms_store(workspace_name, wms_store)

    def delete_wms_store(
        self, workspace_name: str, wms_store_name: str
    ) -> tuple[str, int]:
        """
        Delete a WMS store recursively
        """
        return self.rest_service.delete_wms_store(workspace_name, wms_store_name)

    def get_wms_layer(
        self, workspace_name: str, wms_store_name: str, wms_layer_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a WMS layer by workspace, store and name
        """
        wms_layer, status_code = self.rest_service.get_wms_layer(
            workspace_name, wms_store_name, wms_layer_name
        )
        if isinstance(wms_layer, str):
            return wms_layer, status_code
        return wms_layer.asdict(), status_code

    def create_wms_layer(
        self,
        workspace_name: str,
        wms_store_name: str,
        native_layer_name: str,
        published_layer_name: str | None = None,
    ) -> tuple[str, int]:
        """
        Publish a remote WMS layer
        If it already exists, delete and recreate it (update is not supported by GeoServer)
        """
        published_layer_name = published_layer_name or native_layer_name
        wms_layer = WmsLayer(
            name=published_layer_name,
            native_name=native_layer_name,
            workspace_name=workspace_name,
            store_name=wms_store_name,
        )
        return self.rest_service.create_wms_layer(
            workspace_name, wms_store_name, wms_layer
        )

    def delete_wms_layer(
        self, workspace_name: str, wms_store_name: str, wms_layer_name: str
    ) -> tuple[str, int]:
        """
        Delete a WMS layer
        """
        return self.rest_service.delete_wms_layer(
            workspace_name, wms_store_name, wms_layer_name
        )

    def create_wmts_store(
        self,
        workspace_name: str,
        name: str,
        capabilities: str,
    ) -> tuple[str, int]:
        """
        Create a cascaded WMTS store, or update it if it already exist.
        """
        return self.rest_service.create_wmts_store(workspace_name, name, capabilities)

    def delete_wmts_store(
        self, workspace_name: str, wmts_store_name: str
    ) -> tuple[str, int]:
        """
        Delete a WMTS store recursively
        """
        return self.rest_service.delete_wmts_store(workspace_name, wmts_store_name)

    def get_feature_types(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[list[dict[str, Any]] | str, int]:
        """
        Get all feature types for a given workspace and datastore
        """
        feature_types, status_code = self.rest_service.get_feature_types(
            workspace_name, datastore_name
        )
        if isinstance(feature_types, str):
            return feature_types, status_code
        return feature_types.aslist(), status_code

    def get_feature_type(
        self, workspace_name: str, datastore_name: str, feature_type_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a feature type by workspace, datastore and name
        """
        content, code = self.rest_service.get_feature_type(
            workspace_name, datastore_name, feature_type_name
        )
        if isinstance(content, str):
            return content, code
        return content.asdict(), code

    def get_coverages(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all coverages for a given workspace and coverage store
        """
        coverages, status_code = self.rest_service.get_coverages(
            workspace_name, coveragestore_name
        )
        if isinstance(coverages, str):
            return coverages, status_code
        return coverages.aslist(), status_code

    def get_coverage(
        self, workspace_name: str, coveragestore_name: str, coverage_name: str
    ) -> tuple[dict[str, object] | str, int]:
        """
        Get a single coverage for a given workspace, coverage store, and coverage name
        """
        coverage, status_code = self.rest_service.get_coverage(
            workspace_name, coveragestore_name, coverage_name
        )
        if isinstance(coverage, str):
            return coverage, status_code
        return coverage.asdict(), status_code

    def create_coverage(
        self,
        workspace_name: str,
        coveragestore_name: str,
        coverage_name: str,
        title: str | None = None,
        native_name: str | None = None,
    ) -> tuple[str, int]:
        """
        Publish a coverage layer from a given coverage store
        """
        coverage = Coverage(
            workspace_name=workspace_name,
            store_name=coveragestore_name,
            name=coverage_name,
            title=title or coverage_name,
            native_name=native_name or coverage_name,
        )
        return self.rest_service.create_coverage(coverage)

    def get_coverage_store(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a coverage store by workspace and name
        """
        coverage_store, status_code = self.rest_service.get_coverage_store(
            workspace_name, coveragestore_name
        )
        if isinstance(coverage_store, str):
            return coverage_store, status_code
        return coverage_store.asdict(), status_code

    def create_coverage_store(
        self,
        workspace_name: str,
        coveragestore_name: str,
        url: str,
        type: str = "ImageMosaic",
        enabled: bool = True,
        metadata: dict | None = None,
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Create a coverage store from a store definition. When using a directory path as URL, coverages will be auto-discovered

        :param workspace_name: Name of the workspace
        :param coveragestore_name: Name of the coverage store
        :param url: Directory path on the server or URL of the granules (raster images)
        :param type: Type of the coverage store, e.g. ImageMosaic, GeoTIFF (default: ImageMosaic)
        :param enabled: Whether the coverage store is enabled (default: True)
        :param metadata: Optional metadata dictionary (e.g. {"cogSettings": {"rangeReaderSettings": "HTTP"}})
        """
        return self.rest_service.create_coverage_store(
            CoverageStore(
                workspace_name=workspace_name,
                name=coveragestore_name,
                url=url,
                type=type,
                enabled=enabled,
                metadata=metadata,
            )
        )

    def create_imagemosaic_store_from_directory(
        self, workspace_name: str, coveragestore_name: str, directory_path: str
    ) -> tuple[str, int]:
        """
        Create an ImageMosaic coverage store from a directory on the server which contains granules (raster images).
        Granules and coverages will be auto-discovered. Similar to creating a store from the WebUI.
        Calls /workspaces/{workspace_name}/coveragestores/{coveragestore_name}/external.imagemosaic
        """
        return self.rest_service.create_imagemosaic_store_from_directory(
            workspace_name, coveragestore_name, directory_path
        )

    def create_imagemosaic_store_from_properties_zip(
        self, workspace_name: str, coveragestore_name: str, properties_zip: bytes
    ) -> tuple[str, int]:
        """
        Upload an ImageMosaic coverage store configuration as ZIP to create an empty coverage store.
        The ZIP contains two files: indexer.properties and datastore.properties
        Calls /workspaces/{workspace_name}/coveragestores/{coveragestore_name}/file.imagemosaic?configure=none
        """
        return self.rest_service.create_imagemosaic_store_from_properties_zip(
            workspace_name, coveragestore_name, properties_zip
        )

    def publish_granule_to_coverage_store(
        self,
        workspace_name: str,
        coveragestore_name: str,
        method: str,
        granule_path: str,
    ) -> tuple[str, int]:
        """
        Publish a single granule (raster image) to an existing ImageMosaic coverage store.
        The granule is an existing file stored either on the server or remotely.

        :param workspace_name: Name of the workspace
        :param coveragestore_name: Name of the coverage store
        :param method: "external" for a file on the server, "remote" for a remote file
        :param granule_path: file path (for external granules) or URL (for remote granules)
        """
        if method not in ["external", "remote"]:
            raise ValueError(
                "Unsupported method, must be either 'external' or 'remote'"
            )
        return self.rest_service.publish_granule_to_coverage_store(
            workspace_name, coveragestore_name, method, granule_path
        )

    def harvest_granules_to_coverage_store(
        self, workspace_name: str, coveragestore_name: str, directory_path: str
    ) -> tuple[str, int]:
        """
        Harvest granules (raster files) from a server directory into an existing ImageMosaic coverage store
        """
        return self.rest_service.harvest_granules_to_coverage_store(
            workspace_name, coveragestore_name, directory_path
        )

    def delete_coverage_store(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[str, int]:
        """
        Delete a coverage store recursively
        """
        return self.rest_service.delete_coverage_store(
            workspace_name, coveragestore_name
        )

    def create_feature_type(
        self,
        layer_name: str,
        workspace_name: str | None = None,
        datastore_name: str | None = None,
        title: str | dict | None = None,
        abstract: str | dict | None = None,
        attributes: dict | None = None,
        epsg: int = 4326,
        keywords: list[str] = [],
        time_dimension_info: TimeDimensionInfo | None = None,
    ) -> tuple[str, int]:
        """
        Create a feature type or update it if it already exists.

        :param layer_name: Name of the feature type / layer
        :type layer_name: str
        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name for the datastore
        :type datastore_name: str
        :param title: Title for the feature type (can be internationalized as dict)
        :type title: str or dict, optional
        :param abstract: Abstract for the feature type (can be internationalized as dict)
        :type abstract: str or dict, optional
        :param attributes: Dict defining the feature type attributes (name and type). If omitted, GeoServer will infer the attributes from the native table
        :type attributes: dict, optional
        :param epsg: EPSG code for the feature type SRS (default: 4326)
        :type epsg: int, optional
        :param keywords: List of keywords for the feature type
        :type keywords: list of str, optional
        :param time_dimension_info: Time dimension configuration for the feature type
        :type time_dimension_info: TimeDimensionInfo, optional

        :return: Tuple of (datastore_name, status_code)
        :rtype: tuple

        :Example:

        >>> create_feature_type(
        ...     layer_name="mylayer",
        ...     workspace_name="myworkspace",
        ...     datastore_name="mystore",
        ...     title={"en": "English Title"},
        ...     abstract={"en": "English Abstract"},
        ...     attributes={
        ...         "geom": {
        ...             "type": "Point",
        ...             "required": True,
        ...         },
        ...         "id": {
        ...             "type": "integer",
        ...             "required": True,
        ...         },
        ...         "title": {
        ...             "type": "string",
        ...             "required": False,
        ...              },
        ...         "timestamp": {
        ...             "type": "datetime",
        ...             "required": False,
        ...         },
        ...     },
        ...     epsg=4326,
        ...     keywords=["example"],
        ...     time_dimension_info=TimeDimensionInfo(
        ...         attribute="timestamp",
        ...         presentation="LIST",
        ...         default_value_strategy="MAXIMUM",
        ...     ),
        ... )
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        datastore_name = datastore_name or self.default_datastore
        if not datastore_name:
            raise ValueError("Datastore not provided")
        feature_type = FeatureType(
            name=layer_name,
            native_name=layer_name,
            workspace_name=workspace_name,
            store_name=datastore_name,
            srs=f"EPSG:{epsg}",
            title=title,
            abstract=abstract,
            attributes=utils.convert_attributes(attributes) if attributes else None,
            epsg_code=epsg,
            keywords=keywords,
            time_dimension_info=time_dimension_info,
        )
        return self.rest_service.create_feature_type(feature_type=feature_type)

    def delete_feature_type(
        self, workspace_name: str, datastore_name: str, layer_name: str
    ) -> tuple[str, int]:
        """
        Delete a feature type and associated layer
        """
        return self.rest_service.delete_feature_type(
            workspace_name, datastore_name, layer_name
        )

    def get_layer_groups(
        self, workspace_name: str
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all layer groups for a given workspace
        """
        layer_groups, status_code = self.rest_service.get_layer_groups(workspace_name)
        if isinstance(layer_groups, str):
            return layer_groups, status_code
        return layer_groups.aslist(), status_code

    def get_layer_group(
        self, workspace_name: str, layer_group_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a layer group by name
        """
        layer_group, status_code = self.rest_service.get_layer_group(
            workspace_name, layer_group_name
        )
        if isinstance(layer_group, str):
            return layer_group, status_code
        return layer_group.asdict(), status_code

    def create_layer_group(
        self,
        group: str,
        workspace_name: str | None,
        layers: list[str] | None = None,
        styles: list[str] | None = None,
        title: str | dict | None = None,
        abstract: str | dict | None = None,
        epsg: int = 4326,
        mode: str = "SINGLE",
        enabled: bool = True,
        advertised: bool = True,
        global_styles: bool = False,
    ) -> tuple[str, int]:
        """
        Create a layer group or update it if it already exists.
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        if mode not in LayerGroup.modes:
            raise ValueError(
                f"Invalid mode: {mode}, possible values are: {LayerGroup.modes}"
            )
        if not layers and not styles:
            raise ValueError(
                "Either layers or styles must be provided for a layer group"
            )

        bounds = {
            "minx": utils.EPSG_BBOX[epsg]["nativeBoundingBox"]["minx"],
            "maxx": utils.EPSG_BBOX[epsg]["nativeBoundingBox"]["maxx"],
            "miny": utils.EPSG_BBOX[epsg]["nativeBoundingBox"]["miny"],
            "maxy": utils.EPSG_BBOX[epsg]["nativeBoundingBox"]["maxy"],
            "crs": f"EPSG:{epsg}",
        }

        publishables = None
        if layers:
            publishables = [f"{workspace_name}:{layer}" for layer in layers]

        formatted_styles = None
        if styles:
            if global_styles:
                formatted_styles = styles
            else:
                formatted_styles = [f"{workspace_name}:{style}" for style in styles]

        layer_group = LayerGroup(
            name=group,
            mode=mode,
            workspace_name=workspace_name,
            title=title,
            abstract=abstract,
            publishables=publishables,
            styles=formatted_styles,
            bounds=bounds,
            enabled=enabled,
            advertised=advertised,
        )
        return self.rest_service.create_layer_group(group, workspace_name, layer_group)

    def delete_layer_group(
        self, workspace_name: str, layer_group_name: str
    ) -> tuple[str, int]:
        """
        Delete a layer group
        """
        return self.rest_service.delete_layer_group(workspace_name, layer_group_name)

    def create_wmts_layer(
        self,
        workspace_name: str,
        wmts_store: str,
        native_layer: str,
        published_layer: str | None = None,
        epsg: int = 4326,
        international_title: dict[str, str] | None = None,
        international_abstract: dict[str, str] | None = None,
    ) -> tuple[str, int]:
        """
        Publish a remote WMTS layer (first delete it if it already exists)
        """
        if not published_layer:
            published_layer = native_layer
        return self.rest_service.create_wmts_layer(
            workspace_name,
            wmts_store,
            native_layer,
            published_layer,
            epsg,
            international_title,
            international_abstract,
        )

    def get_gwc_layer(
        self, workspace_name: str, layer: str
    ) -> tuple[dict[str, Any] | str, int]:
        return self.rest_service.get_gwc_layer(workspace_name, layer)

    def publish_gwc_layer(
        self, workspace_name: str, layer: str, epsg: int = 4326
    ) -> tuple[str, int]:
        return self.rest_service.publish_gwc_layer(workspace_name, layer, epsg)

    def delete_gwc_layer(self, workspace_name: str, layer: str) -> tuple[str, int]:
        return self.rest_service.delete_gwc_layer(workspace_name, layer)

    def get_styles(
        self, workspace_name: str | None = None
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all styles for a given workspace. If no workspace is provided, get all global styles
        """
        content, code = self.rest_service.get_styles(workspace_name)
        if isinstance(content, str):
            return content, code
        return content.aslist(), code

    def get_style_definition(
        self, style: str, workspace_name: str | None = None
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a style definition by name
        """
        content, code = self.rest_service.get_style_definition(style, workspace_name)
        if isinstance(content, str):
            return content, code
        return content.asdict(), code

    def create_style_definition(
        self,
        style_name: str,
        filename: str,
        workspace_name: str | None = None,
        format: str = "sld",
    ) -> tuple[str, int]:
        """Create a style definition"""
        style = Style(
            name=style_name,
            filename=filename,
            workspace_name=workspace_name,
            format=format,
        )
        return self.rest_service.create_style_definition(
            style_name=style_name, style=style, workspace_name=workspace_name
        )

    def create_style_from_string(
        self,
        style_name: str,
        style_string: str,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        """Create a style (SLD) from its definition as a string or update it if it already exists."""
        content, code = self.create_style_definition(
            style_name, f"{style_name}.sld", workspace_name
        )
        if code >= 400:
            return content, code
        return self.rest_service.create_style(
            style_name, style_string.encode("utf-8"), workspace_name, format="sld"
        )

    def create_style_from_file(
        self,
        style_name: str,
        file: str,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        """Create a style from a file, or update it if it already exists.
        Supported file extensions are .sld, .zip and .mbstyle."""
        file_ext = Path(file).suffix.lower()
        if file_ext == ".sld":
            style_format = "sld"
            style_definition_filename = f"{style_name}.sld"
            file_format = "sld"
        elif file_ext == ".zip":
            style_format = "sld"
            style_definition_filename = f"{style_name}.sld"
            file_format = "zip"
        elif file_ext == ".mbstyle":
            style_format = "mbstyle"
            style_definition_filename = f"{style_name}.mbstyle"
            file_format = "mbstyle"
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")
        content, code = self.create_style_definition(
            style_name,
            style_definition_filename,
            workspace_name,
            format=style_format,
        )
        if code >= 400:
            return content, code
        with open(f"{file}", "rb") as fs:
            style: bytes = fs.read()
        return self.rest_service.create_style(
            style_name, style, workspace_name, format=file_format
        )

    def set_default_layer_style(
        self, layer_name: str, workspace_name: str, style: str
    ) -> tuple[str, int]:
        """Set the default style for a layer"""
        layer = Layer(layer_name, default_style_name=style)
        return self.rest_service.update_layer(layer, workspace_name)

    def get_wms_layers(
        self, workspace_name: str, accept_languages: str | None = None
    ) -> Any | dict[str, Any]:
        return self.ows_service.get_wms_layers(workspace_name, accept_languages)

    def get_wfs_layers(self, workspace_name: str) -> Any | dict[str, Any]:
        return self.ows_service.get_wfs_layers(workspace_name)

    def get_map(
        self,
        layers: list[str],
        bbox: tuple[float, float, float, float],
        size: tuple[int, int],
        srs: str = "EPSG:2056",
        format: str = "image/png",
        transparent: bool = True,
        styles: list[str] | None = None,
        language: str | None = None,
    ) -> ResponseWrapper | None:
        """
        WMS GetMap request
        """
        if not self.wms:
            self.create_wms()
        params: dict[str, Any] = {
            "layers": layers,
            "srs": srs,
            "bbox": bbox,
            "size": size,
            "format": format,
            "transparent": transparent,
            "styles": styles,
        }
        if language is not None:
            params["language"] = language
        if self.wms:
            return self.wms.getmap(
                **params,
                timeout=120,
            )
        return None

    def get_feature_info(
        self,
        layers: list[str],
        bbox: tuple[float, float, float, float],
        size: tuple[int, int],
        srs: str = "EPSG:2056",
        info_format: str = "application/json",
        transparent: bool = True,
        styles: list[str] | None = None,
        xy: list[float] = [0, 0],
        workspace_name: str | None = None,
    ) -> ResponseWrapper | None:
        """
        WMS GetFeatureInfo request
        """
        if not self.wms:
            self.create_wms(workspace_name)
        params = {
            "layers": layers,
            "srs": srs,
            "bbox": bbox,
            "size": size,
            "info_format": info_format,
            "transparent": transparent,
            "styles": styles,
            "xy": xy,
        }
        if self.wms:
            return self.wms.getfeatureinfo(
                **params,
            )
        return None

    def get_legend_graphic(
        self,
        layer: str | list[str],
        format: str = "image/png",
        language: str | None = None,
        style: str | None = None,
        workspace_name: str | None = None,
    ) -> Response:
        """
        WMS GetLegendGraphic request
        """
        return self.ows_service.get_legend_graphic(
            layer, format, language, style, workspace_name
        )

    def get_tile(
        self,
        layer: str,
        format: str,
        tile_matrix_set: str,
        tile_matrix: str,
        row: int,
        column: int,
        workspace_name: str | None = None,
    ) -> ResponseWrapper | None:
        """
        WMTS GetTile request

        :param layer: Name of the WMTS layer
        :param format: Image format (e.g. "image/png")
        :param tile_matrix_set: Tile matrix set (e.g. "EPSG:3857")
        :param tile_matrix: Tile matrix (zoom level)
        :param row: Tile row
        :param column: Tile column
        :param workspace_name: Optional workspace name
        :return: owslib.util.ResponseWrapper with the tile image or None
        """
        if not self.wmts:
            self.create_wmts(workspace_name=workspace_name)
        if self.wmts:
            return self.wmts.gettile(
                layer=layer,
                format=format,
                tilematrixset=tile_matrix_set,
                tilematrix=tile_matrix,
                row=row,
                column=column,
            )
        return None

    def get_feature(
        self,
        workspace_name: str,
        type_name: str,
        feature_id: int | None = None,
        max_feature: int | None = None,
        format: str = "application/json",
    ) -> dict[str, Any] | str:
        """WFS GetFeature request
        Return the feature(s) as dict if found, otherwise return the response content as string
        """
        # FIXME: we should consider also the global wfs endpoint
        return self.ows_service.get_feature(
            workspace_name, type_name, feature_id, max_feature, format
        )

    def describe_feature_type(
        self,
        workspace_name: str | None = None,
        type_name: str | None = None,
        format: str = "application/json",
    ) -> dict[str, Any] | str:
        """WFS DescribeFeatureType request
        Return the feature type(s) as dict if found, otherwise return the response content as string
        """
        return self.ows_service.describe_feature_type(workspace_name, type_name, format)

    def get_property_value(
        self,
        workspace_name: str,
        type_name: str,
        property: str,
    ) -> dict | list | str:
        """WFS GetPropertyValue request
        Return the properties as dict (if one feature was found), a list (if multiple features were found),
        an empty dict if no feature was found or the response content as string
        """
        # FIXME: we should consider also the global wfs endpoint
        return self.ows_service.get_property_value(workspace_name, type_name, property)

    def create_user(
        self, user: str, password: str, enabled: bool = True
    ) -> tuple[str, int]:
        """
        Create a GeoServer user
        """
        return self.rest_service.create_user(user, password, enabled)

    def update_user(
        self, user: str, password: str | None = None, enabled: bool | None = None
    ) -> tuple[str, int]:
        """
        Update a GeoServer user
        """
        return self.rest_service.update_user(user, password, enabled)

    def delete_user(self, user: str) -> tuple[str, int]:
        """
        Delete a GeoServer user
        """
        return self.rest_service.delete_user(user)

    def create_role(self, role_name: str) -> tuple[str, int]:
        """
        Create a GeoServer role if it does not already exist
        """
        return self.rest_service.create_role_if_not_exists(role_name)

    def delete_role(self, role_name: str) -> tuple[str, int]:
        """
        Delete a GeoServer role
        """
        return self.rest_service.delete_role(role_name)

    def get_user_roles(self, user: str) -> tuple[list[str] | str, int]:
        """
        Get all roles assigned to a GeoServer user
        """
        return self.rest_service.get_user_roles(user)

    def assign_role_to_user(self, user: str, role: str) -> tuple[str, int]:
        """
        Assign a role to a GeoServer user
        """
        return self.rest_service.assign_role_to_user(user, role)

    def remove_role_from_user(self, user: str, role: str) -> tuple[str, int]:
        """
        Remove a role from a GeoServer user
        """
        return self.rest_service.remove_role_from_user(user, role)

    def create_acl_admin_rule(
        self,
        priority: int = 0,
        access: str = "ADMIN",
        role: str | None = None,
        user: str | None = None,
        workspace_name: str | None = None,
    ) -> tuple[dict | str, int]:
        """
        Create a GeoServer ACL admin rule
        """
        return self.rest_service.create_acl_admin_rule(
            priority, access, role, user, workspace_name
        )

    def delete_acl_admin_rule(self, id: int | str) -> tuple[str, int]:
        """
        Delete a GeoServer ACL admin rule by id
        """
        return self.rest_service.delete_acl_admin_rule(str(id))

    def delete_all_acl_admin_rules(self) -> tuple[str, int]:
        """
        Delete all existing GeoServer ACL admin rules
        """
        return self.rest_service.delete_all_acl_admin_rules()

    def get_acl_rules(self) -> tuple[dict[str, Any] | str, int]:
        """
        Return all GeoServer ACL data rules
        """
        return self.rest_service.get_acl_rules()

    def create_acl_rules_for_requests(
        self,
        requests: list[str],
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        service: str | None = None,
        workspace_name: str | None = None,
    ) -> list[tuple[dict | str, int]]:
        """
        Create ACL rules for multiple type of OGC requests
        """
        return self.rest_service.create_acl_rules_for_requests(
            requests, priority, access, role, service, workspace_name
        )

    def create_acl_rule(
        self,
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        user: str | None = None,
        service: str | None = None,
        request: str | None = None,
        workspace_name: str | None = None,
    ) -> tuple[dict | str, int]:
        """
        Create a GeoServer ACL data rule
        """
        return self.rest_service.create_acl_rule(
            priority, access, role, user, service, request, workspace_name
        )

    def delete_all_acl_rules(self) -> tuple[str, int]:
        """
        Delete all existing GeoServer ACL data rules
        """
        return self.rest_service.delete_all_acl_rules()

    def create_gridset(self, epsg: int) -> tuple[str, int]:
        """
        Create a gridset for GeoWebCache for a given projection
        Supported EPSG codes are 2056, 21781 and 3857
        """
        return self.rest_service.create_gridset(epsg)
