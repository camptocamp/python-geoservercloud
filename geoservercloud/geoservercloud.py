from typing import Any

from owslib.map.wms130 import WebMapService_1_3_0
from owslib.util import ResponseWrapper
from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud import utils
from geoservercloud.models import (
    FeatureType,
    PostGisDataStore,
    Workspace,
)
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
    ) -> None:

        self.url: str = url.strip("/")
        self.user: str = user
        self.password: str = password
        self.auth: tuple[str, str] = (user, password)
        self.rest_service: RestService = RestService(url, self.auth)
        self.ows_service: OwsService = OwsService(url, self.auth)
        self.wms: WebMapService_1_3_0 | None = None
        self.wmts: WebMapTileService | None = None
        self.default_workspace: str | None = None
        self.default_datastore: str | None = None

    def create_wms(self) -> None:
        if self.default_workspace:
            self.wms = self.ows_service.create_wms(self.default_workspace)
        else:
            self.wms = self.ows_service.create_wms()

    def create_wmts(self) -> None:
        self.wmts = self.ows_service.create_wmts()

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

    def publish_workspace(self, workspace_name) -> tuple[str, int]:
        """
        Publish the WMS service for a given workspace
        """
        return self.rest_service.publish_workspace(Workspace(workspace_name))

    def set_default_locale_for_service(
        self, workspace_name: str, locale: str | None
    ) -> tuple[str, int]:
        """
        Set a default language for localized WMS requests
        """
        return self.rest_service.set_default_locale_for_service(
            Workspace(workspace_name), locale
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

    def get_pg_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a datastore by workspace and name
        """
        datastore, status_code = self.rest_service.get_pg_datastore(
            workspace_name, datastore_name
        )
        if isinstance(datastore, str):
            return datastore, status_code
        return datastore.asdict(), status_code

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
        datastore = PostGisDataStore(
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
        content, status_code = self.rest_service.create_pg_datastore(
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
        datastore = PostGisDataStore(
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
        content, code = self.rest_service.create_jndi_datastore(
            workspace_name, datastore
        )

        if set_default_datastore:
            self.default_datastore = datastore_name

        return content, code

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

    def create_feature_type(
        self,
        layer: str,
        workspace_name: str | None = None,
        datastore: str | None = None,
        title: str | dict = "Default title",
        abstract: str | dict = "Default abstract",
        attributes: dict = Templates.geom_point_attribute(),  # TODO: remove default value, because if should be None
        epsg: int = 4326,
        keywords: list[str] = [],
    ) -> tuple[str, int]:
        """
        Create a feature type or update it if it already exist.
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        datastore = datastore or self.default_datastore
        if not datastore:
            raise ValueError("Datastore not provided")
        feature_type = FeatureType(
            name=layer,
            native_name=layer,
            workspace_name=workspace_name,
            store_name=datastore,
            srs=f"EPSG:{epsg}",
            title=title,
            abstract=abstract,
            attributes=utils.convert_attributes(attributes),
            epsg_code=epsg,
            keywords=keywords,
        )
        return self.rest_service.create_feature_type(feature_type=feature_type)

    def create_layer_group(
        self,
        group: str,
        workspace_name: str | None,
        layers: list[str],
        title: str | dict,
        abstract: str | dict,
        epsg: int = 4326,
        mode: str = "SINGLE",
    ) -> tuple[str, int]:
        """
        Create a layer group if it does not already exist.
        """
        workspace_name = workspace_name or self.default_workspace
        if not workspace_name:
            raise ValueError("Workspace not provided")
        return self.rest_service.create_layer_group(
            group, workspace_name, layers, title, abstract, epsg, mode
        )

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
    ) -> tuple[list[str] | str, int]:
        """
        Get all styles for a given workspace. If no workspace is provided, get all global styles
        """
        content, code = self.rest_service.get_styles(workspace_name)
        if isinstance(content, str):
            return content, code
        return content.aslist(), code

    def get_style(
        self, style: str, workspace_name: str | None = None
    ) -> tuple[dict[str, Any] | str, int]:
        """
        Get a specific style
        """
        content, code = self.rest_service.get_style(style, workspace_name)
        if isinstance(content, str):
            return content, code
        return content.asdict(), code

    def create_style_from_file(
        self,
        style: str,
        file: str,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        """Create a style from a file, or update it if it already exists.
        Supported file extensions are .sld and .zip."""
        return self.rest_service.create_style_from_file(style, file, workspace_name)

    def set_default_layer_style(
        self, layer: str, workspace_name: str, style: str
    ) -> tuple[str, int]:
        return self.rest_service.set_default_layer_style(layer, workspace_name, style)

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
    ) -> ResponseWrapper | None:
        """
        WMS GetFeatureInfo request
        """
        if not self.wms:
            self.create_wms()
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
        layer: list[str],
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
        self, layer, format, tile_matrix_set, tile_matrix, row, column
    ) -> ResponseWrapper | None:
        """
        WMTS GetTile request
        """
        if not self.wmts:
            self.create_wmts()
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
