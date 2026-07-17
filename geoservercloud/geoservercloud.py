from pathlib import Path
from typing import Any

from owslib.map.wms130 import WebMapService_1_3_0
from owslib.util import ResponseWrapper
from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud import utils
from geoservercloud.models.common import MetadataLink, TimeDimensionInfo
from geoservercloud.models.coverage import Coverage
from geoservercloud.models.coveragestore import CoverageStore
from geoservercloud.models.datastore import DataStore
from geoservercloud.models.featuretype import FeatureType
from geoservercloud.models.gwclayer import GridSubset, GwcLayer, ParameterFilter
from geoservercloud.models.layer import Layer
from geoservercloud.models.layergroup import LayerGroup
from geoservercloud.models.style import Style
from geoservercloud.models.wmslayer import WmsLayer
from geoservercloud.models.wmssettings import WmsSettings
from geoservercloud.models.wmsstore import WmsStore
from geoservercloud.models.wmtsstore import WmtsStore
from geoservercloud.models.workspace import Workspace
from geoservercloud.services import OwsService, RestService


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
        """
        Initialize a WMS OWSLib client scoped to the given workspace

        :param workspace: Name of the workspace, or None to use the default workspace
        :type workspace: str, optional
        """
        if workspace:
            self.wms = self.ows_service.create_wms(workspace)
        elif self.default_workspace:
            self.wms = self.ows_service.create_wms(self.default_workspace)
        else:
            self.wms = self.ows_service.create_wms()

    def create_wmts(self, workspace_name: str | None = None) -> None:
        """
        Initialize a WMTS OWSLib client scoped to the given workspace

        :param workspace_name: Name of the workspace, or None to use the default workspace
        :type workspace_name: str, optional
        """
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

        :return: Tuple of (workspaces, status_code)
        :rtype: tuple
        """
        workspaces, status_code = self.rest_service.get_workspaces()
        if isinstance(workspaces, str):
            return workspaces, status_code
        return workspaces.aslist(), status_code

    def get_workspace(self, workspace_name: str) -> tuple[dict[str, str] | str, int]:
        """
        Get a workspace by name

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Tuple of (workspace, status_code)
        :rtype: tuple
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
        If it exists, update it.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param isolated: Whether the workspace should be isolated (default: False)
        :type isolated: bool, optional
        :param set_default_workspace: Whether to set as the default workspace (default: False)
        :type set_default_workspace: bool, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        workspace = Workspace(workspace_name, isolated)
        content, status_code = self.rest_service.create_workspace(workspace)
        if set_default_workspace:
            self.default_workspace = workspace_name
        return content, status_code

    def delete_workspace(self, workspace_name: str) -> tuple[str, int]:
        """
        Delete a GeoServer workspace (recursively)

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param isolated: Whether the workspace should be isolated (default: False)
        :type isolated: bool, optional
        :param set_default_workspace: Whether to set as the default workspace (default: False)
        :type set_default_workspace: bool, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Tuple of (wms_settings, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param versions: WMS versions to enable (default: ["1.1.1", "1.3.0"])
        :type versions: list of str, optional
        :param cite_compliant: Whether the service should be CITE compliant (default: False)
        :type cite_compliant: bool, optional
        :param schema_base_url: Base URL for OGC schemas (default: "http://schemas.opengis.net")
        :type schema_base_url: str, optional
        :param verbose: Enable verbose XML output (default: False)
        :type verbose: bool, optional
        :param bbox_for_each_crs: Whether to compute the bounding box for each supported CRS (default: False)
        :type bbox_for_each_crs: bool, optional
        :param watermark: Watermark configuration (default: disabled)
        :type watermark: dict, optional
        :param interpolation: Default interpolation method (default: "Nearest")
        :type interpolation: str, optional
        :param get_feature_info_mime_type_checking_enabled: Restrict allowed MIME types for GetFeatureInfo (default: False)
        :type get_feature_info_mime_type_checking_enabled: bool, optional
        :param get_map_mime_type_checking_enabled: Restrict allowed MIME types for GetMap (default: False)
        :type get_map_mime_type_checking_enabled: bool, optional
        :param dynamic_styling_disabled: Disable the SLD_BODY parameter in requests (default: False)
        :type dynamic_styling_disabled: bool, optional
        :param features_reprojection_disabled: Disable on-the-fly feature reprojection (default: False)
        :type features_reprojection_disabled: bool, optional
        :param max_buffer: Maximum buffer size in pixels for rendering, 0 for unlimited (default: 0)
        :type max_buffer: int, optional
        :param max_request_memory: Maximum memory in KB usable per request, 0 for unlimited (default: 0)
        :type max_request_memory: int, optional
        :param max_rendering_time: Maximum rendering time in seconds, 0 for unlimited (default: 0)
        :type max_rendering_time: int, optional
        :param max_rendering_errors: Maximum number of rendering errors tolerated, 0 for unlimited (default: 0)
        :type max_rendering_errors: int, optional
        :param max_requested_dimension_values: Maximum number of dimension values that can be requested (default: 100)
        :type max_requested_dimension_values: int, optional
        :param cache_configuration: GetMap caching configuration (default: disabled)
        :type cache_configuration: dict, optional
        :param remote_style_max_request_time: Maximum time in ms allowed to fetch a remote style (default: 60000)
        :type remote_style_max_request_time: int, optional
        :param remote_style_timeout: Timeout in ms for fetching a remote style (default: 30000)
        :type remote_style_timeout: int, optional
        :param default_group_style_enabled: Whether a default style is generated for layer groups (default: True)
        :type default_group_style_enabled: bool, optional
        :param transform_feature_info_disabled: Disable XSLT transformation of GetFeatureInfo output (default: False)
        :type transform_feature_info_disabled: bool, optional
        :param auto_escape_template_values: Automatically escape template values in GetFeatureInfo output (default: False)
        :type auto_escape_template_values: bool, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param locale: Locale code to set as default (e.g. "en"), or None to unset
        :type locale: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        wms_settings = WmsSettings(default_locale=locale)
        return self.rest_service.put_workspace_wms_settings(
            workspace_name, wms_settings
        )

    def unset_default_locale_for_service(self, workspace_name) -> tuple[str, int]:
        """
        Remove the default language for localized WMS requests

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.set_default_locale_for_service(workspace_name, None)

    def get_datastores(
        self, workspace_name: str
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all datastores for a given workspace

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Tuple of (datastores, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the datastore
        :type datastore_name: str
        :return: Tuple of (datastore, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the datastore
        :type datastore_name: str
        :return: Tuple of (datastore, status_code)
        :rtype: tuple
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
        Create a PostGIS datastore from the DB connection parameters, or update it if it already exists.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name for the datastore
        :type datastore_name: str
        :param pg_host: PostgreSQL host
        :type pg_host: str
        :param pg_port: PostgreSQL port
        :type pg_port: int
        :param pg_db: PostgreSQL database name
        :type pg_db: str
        :param pg_user: PostgreSQL user
        :type pg_user: str
        :param pg_password: PostgreSQL password
        :type pg_password: str
        :param pg_schema: PostgreSQL schema (default: "public")
        :type pg_schema: str, optional
        :param description: Optional description
        :type description: str, optional
        :param set_default_datastore: Whether to set as default datastore (default: False)
        :type set_default_datastore: bool, optional

        :return: Tuple of (datastore_name, status_code)
        :rtype: tuple
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
        Create a PostGIS datastore from a JNDI resource, or update it if it already exists.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name for the datastore
        :type datastore_name: str
        :param jndi_reference: JNDI resource reference name
        :type jndi_reference: str
        :param pg_schema: PostgreSQL schema (default: "public")
        :type pg_schema: str, optional
        :param description: Optional description
        :type description: str, optional
        :param set_default_datastore: Whether to set as default datastore (default: False)
        :type set_default_datastore: bool, optional

        :return: Tuple of (datastore_name, status_code)
        :rtype: tuple
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

    def delete_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[str, int]:
        """
        Delete a datastore recursively

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the datastore
        :type datastore_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_datastore(workspace_name, datastore_name)

    def get_wms_store(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a WMS store by workspace and name

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the WMS store
        :type datastore_name: str
        :return: Tuple of (wms_store, status_code)
        :rtype: tuple
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
        Create a cascaded WMS store, or update it if it already exists.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wms_store_name: Name for the WMS store
        :type wms_store_name: str
        :param capabilities_url: URL of the remote WMS GetCapabilities document
        :type capabilities_url: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wms_store_name: Name of the WMS store
        :type wms_store_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_wms_store(workspace_name, wms_store_name)

    def get_wms_layer(
        self, workspace_name: str, wms_store_name: str, wms_layer_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a WMS layer by workspace, store and name

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wms_store_name: Name of the WMS store
        :type wms_store_name: str
        :param wms_layer_name: Name of the WMS layer
        :type wms_layer_name: str
        :return: Tuple of (wms_layer, status_code)
        :rtype: tuple
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
        Publish a remote WMS layer.
        If it already exists, delete and recreate it (update is not supported by GeoServer)

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wms_store_name: Name of the WMS store
        :type wms_store_name: str
        :param native_layer_name: Name of the layer on the remote WMS server
        :type native_layer_name: str
        :param published_layer_name: Name for the published layer (default: same as native_layer_name)
        :type published_layer_name: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wms_store_name: Name of the WMS store
        :type wms_store_name: str
        :param wms_layer_name: Name of the WMS layer
        :type wms_layer_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_wms_layer(
            workspace_name, wms_store_name, wms_layer_name
        )

    def create_wmts_store(
        self,
        workspace_name: str,
        name: str,
        capabilities: str,
        enabled: bool = True,
        default: bool | None = None,
        disable_on_conn_failure: bool | None = None,
        use_connection_pooling: bool | None = True,
        max_connections: int | None = None,
        read_timeout: int | None = None,
        connect_timeout: int | None = None,
    ) -> tuple[str, int]:
        """
        Create a cascaded WMTS store, or update it if it already exists.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param name: Name for the WMTS store
        :type name: str
        :param capabilities: URL of the remote WMTS GetCapabilities document
        :type capabilities: str
        :param enabled: Whether the store should be enabled (default: True)
        :type enabled: bool, optional
        :param default: Whether this is the default WMTS store
        :type default: bool, optional
        :param disable_on_conn_failure: Disable the store on connection failure
        :type disable_on_conn_failure: bool, optional
        :param use_connection_pooling: Whether to use connection pooling (default: True)
        :type use_connection_pooling: bool, optional
        :param max_connections: Maximum number of connections
        :type max_connections: int, optional
        :param read_timeout: Read timeout in seconds
        :type read_timeout: int, optional
        :param connect_timeout: Connect timeout in seconds
        :type connect_timeout: int, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        wmts_store = WmtsStore(
            workspace_name=workspace_name,
            name=name,
            capabilities_url=capabilities,
            enabled=enabled,
            default=default,
            disable_on_conn_failure=disable_on_conn_failure,
            use_connection_pooling=use_connection_pooling,
            max_connections=max_connections,
            read_timeout=read_timeout,
            connect_timeout=connect_timeout,
        )
        return self.rest_service.create_wmts_store(workspace_name, wmts_store)

    def delete_wmts_store(
        self, workspace_name: str, wmts_store_name: str
    ) -> tuple[str, int]:
        """
        Delete a WMTS store recursively

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wmts_store_name: Name of the WMTS store
        :type wmts_store_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_wmts_store(workspace_name, wmts_store_name)

    def get_feature_types(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[list[dict[str, Any]] | str, int]:
        """
        Get all feature types for a given workspace and datastore

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the datastore
        :type datastore_name: str
        :return: Tuple of (feature_types, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the datastore
        :type datastore_name: str
        :param feature_type_name: Name of the feature type
        :type feature_type_name: str
        :return: Tuple of (feature_type, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :return: Tuple of (coverages, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param coverage_name: Name of the coverage
        :type coverage_name: str
        :return: Tuple of (coverage, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param coverage_name: Name for the coverage
        :type coverage_name: str
        :param title: Optional title for the coverage (default: same as coverage_name)
        :type title: str, optional
        :param native_name: Native name of the coverage (default: same as coverage_name)
        :type native_name: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :return: Tuple of (coverage_store, status_code)
        :rtype: tuple
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
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param url: Directory path on the server or URL of the granules (raster images)
        :type url: str
        :param type: Type of the coverage store, e.g. ImageMosaic, GeoTIFF (default: "ImageMosaic")
        :type type: str, optional
        :param enabled: Whether the coverage store is enabled (default: True)
        :type enabled: bool, optional
        :param metadata: Optional metadata dictionary (e.g. {"cogSettings": {"rangeReaderSettings": "HTTP"}})
        :type metadata: dict, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param directory_path: Directory path on the server containing the granules
        :type directory_path: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param properties_zip: ZIP archive content containing indexer.properties and datastore.properties
        :type properties_zip: bytes
        :return: Tuple of (content, status_code)
        :rtype: tuple
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
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param method: "external" for a file on the server, "remote" for a remote file
        :type method: str
        :param granule_path: file path (for external granules) or URL (for remote granules)
        :type granule_path: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :param directory_path: Directory path on the server containing the granules
        :type directory_path: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.harvest_granules_to_coverage_store(
            workspace_name, coveragestore_name, directory_path
        )

    def delete_coverage_store(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[str, int]:
        """
        Delete a coverage store recursively

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param coveragestore_name: Name of the coverage store
        :type coveragestore_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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
        keywords: list[str] | None = None,
        time_dimension_info: TimeDimensionInfo | None = None,
        layer_links: list[dict[str, str]] | None = None,
        native_name: str | None = None,
        cql_filter: str | None = None,
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
        :param layer_links: List of metadata links for the feature type, e.g. [{'content':"mymetadataurl", 'metadataType':"ISO19115:2003", 'type':"text/xml"}]
        :type layer_links: list of dict, optional
        :param native_name: Native name of the feature type (default: same as layer_name)
        :type native_name: str, optional
        :param cql_filter: CQL filter to filter the data, e.g. key='Value'
        :type cql_filter: str, optional
        :return: Tuple of (datastore_name, status_code)
        :rtype: tuple

        :Example:

        >>> create_feature_type(
        ...     layer_name="mylayer",
        ...     workspace_name="myworkspace",
        ...     datastore_name="mystore",
        ...     native_name="nativename",
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
        ...     layer_links=[{'content':"mymetadataurl", 'metadataType':"ISO19115:2003", 'type':"text/xml"}],
        ...     cql_filter="key='Value'"
        ... )
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        datastore_name = datastore_name or self.default_datastore
        if not datastore_name:
            raise ValueError("Datastore not provided")
        metadata_links = [
            MetadataLink(
                url=link["content"],
                metadata_type=link["metadataType"],
                mime_type=link["type"],
            )
            for link in (layer_links or [])
        ]
        feature_type = FeatureType(
            name=layer_name,
            native_name=native_name or layer_name,
            workspace_name=workspace_name,
            store_name=datastore_name,
            srs=f"EPSG:{epsg}",
            title=title,
            abstract=abstract,
            attributes=utils.convert_attributes(attributes) if attributes else None,
            epsg_code=epsg,
            keywords=keywords,
            time_dimension_info=time_dimension_info,
            metadata_links=metadata_links,
            cql_filter=cql_filter,
        )
        return self.rest_service.create_feature_type(feature_type=feature_type)

    def delete_feature_type(
        self, workspace_name: str, datastore_name: str, layer_name: str
    ) -> tuple[str, int]:
        """
        Delete a feature type and associated layer

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param datastore_name: Name of the datastore
        :type datastore_name: str
        :param layer_name: Name of the feature type / layer
        :type layer_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_feature_type(
            workspace_name, datastore_name, layer_name
        )

    def get_layer_groups(
        self, workspace_name: str
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all layer groups for a given workspace

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Tuple of (layer_groups, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param layer_group_name: Name of the layer group
        :type layer_group_name: str
        :return: Tuple of (layer_group, status_code)
        :rtype: tuple
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
        Create a layer group, or update it if it already exists.

        :param group: Name for the layer group
        :type group: str
        :param workspace_name: Name of the workspace
        :type workspace_name: str, optional
        :param layers: List of layer names to include in the group
        :type layers: list of str, optional
        :param styles: List of style names associated with each layer
        :type styles: list of str, optional
        :param title: Title for the layer group (can be internationalized as dict)
        :type title: str or dict, optional
        :param abstract: Abstract for the layer group (can be internationalized as dict)
        :type abstract: str or dict, optional
        :param epsg: EPSG code used to compute the layer group bounds (default: 4326)
        :type epsg: int, optional
        :param mode: Layer group mode, e.g. "SINGLE", "NAMED", "CONTAINER", "EO" (default: "SINGLE")
        :type mode: str, optional
        :param enabled: Whether the layer group is enabled (default: True)
        :type enabled: bool, optional
        :param advertised: Whether the layer group is advertised (default: True)
        :type advertised: bool, optional
        :param global_styles: Whether the provided styles are global styles rather than workspace styles (default: False)
        :type global_styles: bool, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param layer_group_name: Name of the layer group
        :type layer_group_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param wmts_store: Name of the WMTS store
        :type wmts_store: str
        :param native_layer: Name of the layer on the remote WMTS server
        :type native_layer: str
        :param published_layer: Name for the published layer (default: same as native_layer)
        :type published_layer: str, optional
        :param epsg: EPSG code for the layer SRS (default: 4326)
        :type epsg: int, optional
        :param international_title: Internationalized title, e.g. {"en": "English Title"}
        :type international_title: dict, optional
        :param international_abstract: Internationalized abstract, e.g. {"en": "English Abstract"}
        :type international_abstract: dict, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
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
        """
        Get a GeoWebCache layer by workspace and layer name

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param layer: Name of the layer
        :type layer: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.get_gwc_layer(workspace_name, layer)

    def publish_gwc_layer(
        self,
        workspace_name: str,
        layer: str,
        epsg: int = 4326,
        id: str | None = None,
        enabled: bool = True,
        grid_subsets: list[GridSubset] | None = None,
        mime_formats: list[str] | None = None,
        parameter_filters: list[ParameterFilter] | None = None,
        meta_width_height: list[int] | None = None,
        gutter: int | None = None,
        expire_cache: int | None = None,
        expire_clients: int | None = None,
        cache_warning_skips: list[Any] | None = None,
    ) -> tuple[str, int]:
        """
        Publish a GeoWebCache layer, or update it if it already exists.

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param layer: Name of the layer to cache
        :type layer: str
        :param epsg: EPSG code used to derive the default grid subset (default: 4326)
        :type epsg: int, optional
        :param id: Optional GeoWebCache layer id
        :type id: str, optional
        :param enabled: Whether the cached layer is enabled (default: True)
        :type enabled: bool, optional
        :param grid_subsets: List of grid subsets to cache (default: derived from epsg)
        :type grid_subsets: list of GridSubset, optional
        :param mime_formats: List of MIME types to cache, e.g. ["image/png"]
        :type mime_formats: list of str, optional
        :param parameter_filters: List of parameter filters applied to the cache
        :type parameter_filters: list of ParameterFilter, optional
        :param meta_width_height: Meta-tiling factors as [width, height]
        :type meta_width_height: list of int, optional
        :param gutter: Gutter size in pixels
        :type gutter: int, optional
        :param expire_cache: Cache expiration time in seconds
        :type expire_cache: int, optional
        :param expire_clients: Client cache expiration time in seconds
        :type expire_clients: int, optional
        :param cache_warning_skips: List of warnings to skip when seeding the cache
        :type cache_warning_skips: list, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        gwc_layer = GwcLayer(
            workspace_name=workspace_name,
            layer_name=layer,
            id=id,
            enabled=enabled,
            grid_subsets=grid_subsets or [GridSubset(grid_set_name=f"EPSG:{epsg}")],
            mime_formats=mime_formats,
            parameter_filters=parameter_filters,
            meta_width_height=meta_width_height,
            gutter=gutter,
            expire_cache=expire_cache,
            expire_clients=expire_clients,
            cache_warning_skips=cache_warning_skips,
        )
        return self.rest_service.publish_gwc_layer(gwc_layer)

    def delete_gwc_layer(self, workspace_name: str, layer: str) -> tuple[str, int]:
        """
        Delete a GeoWebCache layer

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param layer: Name of the layer
        :type layer: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_gwc_layer(workspace_name, layer)

    def get_styles(
        self, workspace_name: str | None = None
    ) -> tuple[list[dict[str, str]] | str, int]:
        """
        Get all styles for a given workspace. If no workspace is provided, get all global styles

        :param workspace_name: Name of the workspace, or None for global styles
        :type workspace_name: str, optional
        :return: Tuple of (styles, status_code)
        :rtype: tuple
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

        :param style: Name of the style
        :type style: str
        :param workspace_name: Name of the workspace, or None for a global style
        :type workspace_name: str, optional
        :return: Tuple of (style_definition, status_code)
        :rtype: tuple
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
        """
        Create a style definition, or update it if it already exists.

        :param style_name: Name for the style
        :type style_name: str
        :param filename: Filename of the style resource, e.g. "mystyle.sld"
        :type filename: str
        :param workspace_name: Name of the workspace, or None for a global style
        :type workspace_name: str, optional
        :param format: Style format, e.g. "sld" or "mbstyle" (default: "sld")
        :type format: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
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
        """
        Create a style (SLD) from its definition as a string, or update it if it already exists.

        :param style_name: Name for the style
        :type style_name: str
        :param style_string: SLD style definition as a string
        :type style_string: str
        :param workspace_name: Name of the workspace, or None for a global style
        :type workspace_name: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
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
        """
        Create a style from a file, or update it if it already exists.
        Supported file extensions are .sld, .zip and .mbstyle.

        :param style_name: Name for the style
        :type style_name: str
        :param file: Path to the style file (.sld, .zip or .mbstyle)
        :type file: str
        :param workspace_name: Name of the workspace, or None for a global style
        :type workspace_name: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
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
        """
        Set the default style for a layer

        :param layer_name: Name of the layer
        :type layer_name: str
        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param style: Name of the style to set as default
        :type style: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        layer = Layer(layer_name, default_style_name=style)
        return self.rest_service.update_layer(layer, workspace_name)

    def get_wms_layers(
        self, workspace_name: str, accept_languages: str | None = None
    ) -> Any | dict[str, Any]:
        """
        Get the capabilities of all WMS layers for a given workspace

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param accept_languages: Optional comma-separated list of preferred languages for localized content
        :type accept_languages: str, optional
        :return: Parsed WMS capabilities document
        :rtype: Any or dict
        """
        return self.ows_service.get_wms_layers(workspace_name, accept_languages)

    def get_wfs_layers(self, workspace_name: str) -> Any | dict[str, Any]:
        """
        Get the capabilities of all WFS layers for a given workspace

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :return: Parsed WFS capabilities document
        :rtype: Any or dict
        """
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
        time: str | None = None,
    ) -> ResponseWrapper | None:
        """
        WMS GetMap request

        :param layers: List of layer names to render
        :type layers: list of str
        :param bbox: Bounding box as (minx, miny, maxx, maxy)
        :type bbox: tuple of float
        :param size: Image size as (width, height) in pixels
        :type size: tuple of int
        :param srs: Spatial reference system (default: "EPSG:2056")
        :type srs: str, optional
        :param format: Image format (default: "image/png")
        :type format: str, optional
        :param transparent: Whether the background should be transparent (default: True)
        :type transparent: bool, optional
        :param styles: List of style names to apply to the layers
        :type styles: list of str, optional
        :param language: Optional language code for localized content
        :type language: str, optional
        :param time: Optional time value for time-enabled layers
        :type time: str, optional
        :return: owslib.util.ResponseWrapper with the map image, or None
        :rtype: ResponseWrapper, optional
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
            "time": time,
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
        time: str | None = None,
        workspace_name: str | None = None,
    ) -> ResponseWrapper | None:
        """
        WMS GetFeatureInfo request

        :param layers: List of layer names to query
        :type layers: list of str
        :param bbox: Bounding box as (minx, miny, maxx, maxy)
        :type bbox: tuple of float
        :param size: Image size as (width, height) in pixels
        :type size: tuple of int
        :param srs: Spatial reference system (default: "EPSG:2056")
        :type srs: str, optional
        :param info_format: Format of the returned feature info (default: "application/json")
        :type info_format: str, optional
        :param transparent: Whether the background should be transparent (default: True)
        :type transparent: bool, optional
        :param styles: List of style names to apply to the layers
        :type styles: list of str, optional
        :param xy: Pixel coordinates (x, y) to query (default: [0, 0])
        :type xy: list of float, optional
        :param time: Optional time value for time-enabled layers
        :type time: str, optional
        :param workspace_name: Optional workspace name
        :type workspace_name: str, optional
        :return: owslib.util.ResponseWrapper with the feature info, or None
        :rtype: ResponseWrapper, optional
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
            "time": time,
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

        :param layer: Name of the layer(s) to get a legend for
        :type layer: str or list of str
        :param format: Image format (default: "image/png")
        :type format: str, optional
        :param language: Optional language code for localized content
        :type language: str, optional
        :param style: Optional style name to use for the legend
        :type style: str, optional
        :param workspace_name: Optional workspace name
        :type workspace_name: str, optional
        :return: HTTP response with the legend image
        :rtype: requests.Response
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
        """
        WFS GetFeature request
        Return the feature(s) as dict if found, otherwise return the response content as string

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param type_name: Name of the feature type
        :type type_name: str
        :param feature_id: Optional feature id to fetch a single feature
        :type feature_id: int, optional
        :param max_feature: Maximum number of features to return
        :type max_feature: int, optional
        :param format: Response format (default: "application/json")
        :type format: str, optional
        :return: Feature(s) as a dict, or the response content as a string
        :rtype: dict or str
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
        """
        WFS DescribeFeatureType request
        Return the feature type(s) as dict if found, otherwise return the response content as string

        :param workspace_name: Optional workspace name
        :type workspace_name: str, optional
        :param type_name: Optional name of the feature type
        :type type_name: str, optional
        :param format: Response format (default: "application/json")
        :type format: str, optional
        :return: Feature type(s) as a dict, or the response content as a string
        :rtype: dict or str
        """
        return self.ows_service.describe_feature_type(workspace_name, type_name, format)

    def get_property_value(
        self,
        workspace_name: str,
        type_name: str,
        property: str,
    ) -> dict | list | str:
        """
        WFS GetPropertyValue request
        Return the properties as dict (if one feature was found), a list (if multiple features were found),
        an empty dict if no feature was found or the response content as string

        :param workspace_name: Name of the workspace
        :type workspace_name: str
        :param type_name: Name of the feature type
        :type type_name: str
        :param property: Name of the property to fetch
        :type property: str
        :return: Property value(s) as a dict or list, or the response content as a string
        :rtype: dict or list or str
        """
        # FIXME: we should consider also the global wfs endpoint
        return self.ows_service.get_property_value(workspace_name, type_name, property)

    def create_user(
        self, user: str, password: str, enabled: bool = True
    ) -> tuple[str, int]:
        """
        Create a GeoServer user

        :param user: Username
        :type user: str
        :param password: Password for the user
        :type password: str
        :param enabled: Whether the user should be enabled (default: True)
        :type enabled: bool, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.create_user(user, password, enabled)

    def update_user(
        self, user: str, password: str | None = None, enabled: bool | None = None
    ) -> tuple[str, int]:
        """
        Update a GeoServer user

        :param user: Username
        :type user: str
        :param password: New password for the user
        :type password: str, optional
        :param enabled: Whether the user should be enabled
        :type enabled: bool, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.update_user(user, password, enabled)

    def delete_user(self, user: str) -> tuple[str, int]:
        """
        Delete a GeoServer user

        :param user: Username
        :type user: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_user(user)

    def create_role(self, role_name: str) -> tuple[str, int]:
        """
        Create a GeoServer role if it does not already exist

        :param role_name: Name of the role
        :type role_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.create_role_if_not_exists(role_name)

    def delete_role(self, role_name: str) -> tuple[str, int]:
        """
        Delete a GeoServer role

        :param role_name: Name of the role
        :type role_name: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_role(role_name)

    def get_user_roles(self, user: str) -> tuple[list[str] | str, int]:
        """
        Get all roles assigned to a GeoServer user

        :param user: Username
        :type user: str
        :return: Tuple of (roles, status_code)
        :rtype: tuple
        """
        return self.rest_service.get_user_roles(user)

    def assign_role_to_user(self, user: str, role: str) -> tuple[str, int]:
        """
        Assign a role to a GeoServer user

        :param user: Username
        :type user: str
        :param role: Name of the role
        :type role: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.assign_role_to_user(user, role)

    def remove_role_from_user(self, user: str, role: str) -> tuple[str, int]:
        """
        Remove a role from a GeoServer user

        :param user: Username
        :type user: str
        :param role: Name of the role
        :type role: str
        :return: Tuple of (content, status_code)
        :rtype: tuple
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

        :param priority: Rule priority (default: 0)
        :type priority: int, optional
        :param access: Access level, e.g. "ADMIN" (default: "ADMIN")
        :type access: str, optional
        :param role: Optional role the rule applies to
        :type role: str, optional
        :param user: Optional user the rule applies to
        :type user: str, optional
        :param workspace_name: Optional workspace the rule applies to
        :type workspace_name: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.create_acl_admin_rule(
            priority, access, role, user, workspace_name
        )

    def delete_acl_admin_rule(self, id: int | str) -> tuple[str, int]:
        """
        Delete a GeoServer ACL admin rule by id

        :param id: Id of the ACL admin rule
        :type id: int or str
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_acl_admin_rule(str(id))

    def delete_all_acl_admin_rules(self) -> tuple[str, int]:
        """
        Delete all existing GeoServer ACL admin rules

        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_all_acl_admin_rules()

    def get_acl_rules(self) -> tuple[dict[str, Any] | str, int]:
        """
        Return all GeoServer ACL data rules

        :return: Tuple of (rules, status_code)
        :rtype: tuple
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
        Create ACL rules for multiple types of OGC requests

        :param requests: List of request types, e.g. ["GetMap", "GetFeatureInfo"]
        :type requests: list of str
        :param priority: Base priority for the rules (default: 0)
        :type priority: int, optional
        :param access: Access level, e.g. "DENY" (default: "DENY")
        :type access: str, optional
        :param role: Optional role the rules apply to
        :type role: str, optional
        :param service: Optional OGC service the rules apply to, e.g. "WMS"
        :type service: str, optional
        :param workspace_name: Optional workspace the rules apply to
        :type workspace_name: str, optional
        :return: List of tuples of (content, status_code), one per created rule
        :rtype: list of tuple
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

        :param priority: Rule priority (default: 0)
        :type priority: int, optional
        :param access: Access level, e.g. "DENY" (default: "DENY")
        :type access: str, optional
        :param role: Optional role the rule applies to
        :type role: str, optional
        :param user: Optional user the rule applies to
        :type user: str, optional
        :param service: Optional OGC service the rule applies to, e.g. "WMS"
        :type service: str, optional
        :param request: Optional request type the rule applies to, e.g. "GetMap"
        :type request: str, optional
        :param workspace_name: Optional workspace the rule applies to
        :type workspace_name: str, optional
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.create_acl_rule(
            priority, access, role, user, service, request, workspace_name
        )

    def delete_all_acl_rules(self) -> tuple[str, int]:
        """
        Delete all existing GeoServer ACL data rules

        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.delete_all_acl_rules()

    def create_gridset(self, epsg: int) -> tuple[str, int]:
        """
        Create a gridset for GeoWebCache for a given projection
        Supported EPSG codes are 2056, 21781 and 3857

        :param epsg: EPSG code for the gridset
        :type epsg: int
        :return: Tuple of (content, status_code)
        :rtype: tuple
        """
        return self.rest_service.create_gridset(epsg)
