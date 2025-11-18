from json import JSONDecodeError
from pathlib import Path
from typing import Any

from owslib.wmts import WebMapTileService
from requests import Response

from geoservercloud.models.common import BaseModel
from geoservercloud.models.coverage import Coverage
from geoservercloud.models.coverages import Coverages
from geoservercloud.models.coveragestore import CoverageStore
from geoservercloud.models.datastore import PostGisDataStore
from geoservercloud.models.datastores import DataStores
from geoservercloud.models.featuretype import FeatureType
from geoservercloud.models.featuretypes import FeatureTypes
from geoservercloud.models.layer import Layer
from geoservercloud.models.layergroup import LayerGroup
from geoservercloud.models.layergroups import LayerGroups
from geoservercloud.models.resourcedirectory import ResourceDirectory
from geoservercloud.models.style import Style
from geoservercloud.models.styles import Styles
from geoservercloud.models.wmslayer import WmsLayer
from geoservercloud.models.wmssettings import WmsSettings
from geoservercloud.models.wmsstore import WmsStore
from geoservercloud.models.workspace import Workspace
from geoservercloud.models.workspaces import Workspaces
from geoservercloud.services.restclient import RestClient
from geoservercloud.templates import Templates


class RestService:
    """
    Service responsible for serializing and deserializing payloads and routing requests to GeoServer REST API

    Attributes
    ----------
    url : str
        base GeoServer URL
    auth : tuple[str, str]
        username and password for GeoServer
    """

    def __init__(self, url: str, auth: tuple[str, str], verifytls: bool = True) -> None:
        self.url: str = url
        self.auth: tuple[str, str] = auth
        self.rest_client = RestClient(url, auth, verifytls)
        self.acl_endpoints = self.AclEndpoints()
        self.gwc_endpoints = self.GwcEndpoints()
        self.rest_endpoints = self.RestEndpoints()

    def get_workspaces(self) -> tuple[Workspaces | str, int]:
        response: Response = self.rest_client.get(self.rest_endpoints.workspaces())
        return self.deserialize_response(response, Workspaces)

    def get_workspace(self, name: str) -> tuple[Workspace | str, int]:
        response: Response = self.rest_client.get(self.rest_endpoints.workspace(name))
        return self.deserialize_response(response, Workspace)

    def create_workspace(self, workspace: Workspace) -> tuple[str, int]:
        path: str = self.rest_endpoints.workspaces()
        response: Response = self.rest_client.post(path, json=workspace.post_payload())
        if response.status_code == 409:
            path = self.rest_endpoints.workspace(workspace.name)
            response = self.rest_client.put(path, json=workspace.put_payload())
        return response.content.decode(), response.status_code

    def delete_workspace(self, workspace: Workspace) -> tuple[str, int]:
        path: str = self.rest_endpoints.workspace(workspace.name)
        params: dict[str, str] = {"recurse": "true"}
        response: Response = self.rest_client.delete(path, params=params)
        return response.content.decode(), response.status_code

    def get_workspace_wms_settings(
        self, workspace_name: str
    ) -> tuple[WmsSettings | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.workspace_wms_settings(workspace_name)
        )
        return self.deserialize_response(response, WmsSettings)

    def put_workspace_wms_settings(
        self, workspace_name: str, wms_settings: WmsSettings
    ) -> tuple[str, int]:
        response: Response = self.rest_client.put(
            self.rest_endpoints.workspace_wms_settings(workspace_name),
            json=wms_settings.put_payload(),
        )
        return response.content.decode(), response.status_code

    def get_datastores(self, workspace_name: str) -> tuple[DataStores | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.datastores(workspace_name)
        )
        return self.deserialize_response(response, DataStores)

    def get_pg_datastore(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[PostGisDataStore | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.datastore(workspace_name, datastore_name)
        )
        return self.deserialize_response(response, PostGisDataStore)

    def create_pg_datastore(
        self, workspace_name: str, datastore: PostGisDataStore
    ) -> tuple[str, int]:
        if not self.resource_exists(
            self.rest_endpoints.datastore(workspace_name, datastore.name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.datastores(workspace_name),
                json=datastore.post_payload(),
            )
        else:
            response = self.rest_client.put(
                self.rest_endpoints.datastore(workspace_name, datastore.name),
                json=datastore.put_payload(),
            )
        return response.content.decode(), response.status_code

    def create_jndi_datastore(
        self, workspace_name: str, datastore: PostGisDataStore
    ) -> tuple[str, int]:
        if not self.resource_exists(
            self.rest_endpoints.datastore(workspace_name, datastore.name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.datastores(workspace_name),
                json=datastore.post_payload(),
            )
        else:
            response = self.rest_client.put(
                self.rest_endpoints.datastore(workspace_name, datastore.name),
                json=datastore.put_payload(),
            )
        return response.content.decode(), response.status_code

    def get_wms_store(
        self, workspace_name: str, wms_store_name: str
    ) -> tuple[WmsStore | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.wmsstore(workspace_name, wms_store_name)
        )
        return self.deserialize_response(response, WmsStore)

    def create_wms_store(
        self, workspace_name: str, wms_store: WmsStore
    ) -> tuple[str, int]:
        if not self.resource_exists(
            self.rest_endpoints.wmsstore(workspace_name, wms_store.name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.wmsstores(workspace_name),
                json=wms_store.post_payload(),
            )
        else:
            response = self.rest_client.put(
                self.rest_endpoints.wmsstore(workspace_name, wms_store.name),
                json=wms_store.put_payload(),
            )
        return response.content.decode(), response.status_code

    def delete_wms_store(
        self, workspace_name: str, wms_store_name: str
    ) -> tuple[str, int]:
        path = self.rest_endpoints.wmsstore(workspace_name, wms_store_name)
        params: dict[str, str] = {"recurse": "true"}
        response: Response = self.rest_client.delete(path, params=params)
        return response.content.decode(), response.status_code

    def get_wms_layer(
        self, workspace_name: str, wms_store_name: str, wms_layer_name: str
    ) -> tuple[WmsLayer | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.wmslayer(workspace_name, wms_store_name, wms_layer_name)
        )
        return self.deserialize_response(response, WmsLayer)

    def create_wms_layer(
        self, workspace_name: str, wms_store_name: str, wms_layer: WmsLayer
    ) -> tuple[str, int]:
        if self.resource_exists(
            self.rest_endpoints.wmslayer(workspace_name, wms_store_name, wms_layer.name)
        ):
            self.delete_wms_layer(workspace_name, wms_store_name, wms_layer.name)
        response: Response = self.rest_client.post(
            self.rest_endpoints.wmslayers(workspace_name, wms_store_name),
            json=wms_layer.post_payload(),
        )
        return response.content.decode(), response.status_code

    def delete_wms_layer(
        self, workspace_name: str, wms_store_name: str, wms_layer_name: str
    ) -> tuple[str, int]:
        path = self.rest_endpoints.wmslayer(
            workspace_name, wms_store_name, wms_layer_name
        )
        params: dict[str, str] = {"recurse": "true"}
        response: Response = self.rest_client.delete(path, params=params)
        return response.content.decode(), response.status_code

    def create_wmts_store(
        self,
        workspace_name: str,
        name: str,
        capabilities: str,
    ) -> tuple[str, int]:
        payload = Templates.wmts_store(workspace_name, name, capabilities)
        if not self.resource_exists(
            self.rest_endpoints.wmtsstore(workspace_name, name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.wmtsstores(workspace_name), json=payload
            )
        else:
            response = self.rest_client.put(
                self.rest_endpoints.wmtsstore(workspace_name, name), json=payload
            )
        return response.content.decode(), response.status_code

    def delete_wmts_store(
        self, workspace_name: str, wmts_store_name: str
    ) -> tuple[str, int]:
        """
        Delete a WMTS store recursively
        """
        path = self.rest_endpoints.wmtsstore(workspace_name, wmts_store_name)
        params: dict[str, str] = {"recurse": "true"}
        response: Response = self.rest_client.delete(path, params=params)
        return response.content.decode(), response.status_code

    def create_wmts_layer(
        self,
        workspace_name: str,
        wmts_store: str,
        native_layer: str,
        published_layer: str,
        epsg: int = 4326,
        international_title: dict[str, str] | None = None,
        international_abstract: dict[str, str] | None = None,
    ) -> tuple[str, int]:
        resource_path: str = self.rest_endpoints.wmtslayer(
            workspace_name, wmts_store, published_layer
        )
        if self.resource_exists(resource_path):
            self.rest_client.delete(
                resource_path,
                params={"recurse": "true"},
            )
            # Also delete the corresponding GWC layer (delete is not cascaded when using REST API)
            self.delete_gwc_layer(workspace_name, published_layer)
        capabilities_url: str = (
            self.rest_client.get(
                self.rest_endpoints.wmtsstore(workspace_name, wmts_store)
            )
            .json()
            .get("wmtsStore")
            .get("capabilitiesURL")
        )
        wgs84_bbox: tuple[float, float, float, float] | None = self.get_wmts_layer_bbox(
            capabilities_url, native_layer
        )

        payload: dict[str, dict[str, Any]] = Templates.wmts_layer(
            published_layer,
            native_layer,
            wgs84_bbox=wgs84_bbox,
            epsg=epsg,
            international_title=international_title,
            international_abstract=international_abstract,
        )

        response: Response = self.rest_client.post(
            self.rest_endpoints.wmtslayers(workspace_name, wmts_store), json=payload
        )
        return response.content.decode(), response.status_code

    def get_gwc_layer(
        self, workspace_name: str, layer: str
    ) -> tuple[dict[str, Any] | str, int]:
        response: Response = self.rest_client.get(
            self.gwc_endpoints.layer(workspace_name, layer)
        )
        try:
            content = response.json()
        except:
            content = response.content.decode()
        return content, response.status_code

    def publish_gwc_layer(
        self, workspace_name: str, layer: str, epsg: int
    ) -> tuple[str, int]:
        # Reload config to make sure GWC is aware of GeoServer layers
        self.rest_client.post(
            self.gwc_endpoints.reload(),
            headers={"Content-Type": "application/json"},
            data="reload_configuration=1",  # type: ignore
        )
        # Do not re-publish an existing layer
        # TODO: fix template so that we can PUT an existing layer (/!\ check with an OGC client that the
        # layer is not corrupted after the second PUT)
        content, code = self.get_gwc_layer(workspace_name, layer)
        if code == 200:
            return "", code
        payload = Templates.gwc_layer(workspace_name, layer, f"EPSG:{epsg}")
        response: Response = self.rest_client.put(
            self.gwc_endpoints.layer(workspace_name, layer),
            json=payload,
        )
        return response.content.decode(), response.status_code

    def delete_gwc_layer(self, workspace_name: str, layer: str) -> tuple[str, int]:
        response: Response = self.rest_client.delete(
            self.gwc_endpoints.layer(workspace_name, layer)
        )
        return response.content.decode(), response.status_code

    def create_gridset(self, epsg: int) -> tuple[str, int]:
        """
        Create a gridset for GeoWebCache for a given projection
        Supported EPSG codes are 2056, 21781 and 3857
        """
        if self.resource_exists(self.gwc_endpoints.gridset(epsg)):
            return "", 200
        file_path: Path = Path(__file__).parent.parent / "gridsets" / f"{epsg}.xml"
        headers: dict[str, str] = {"Content-Type": "application/xml"}
        try:
            data: bytes = file_path.read_bytes()
        except FileNotFoundError:
            raise ValueError(f"No gridset definition found for EPSG:{epsg}")
        response: Response = self.rest_client.put(
            self.gwc_endpoints.gridset(epsg), data=data, headers=headers
        )
        return response.content.decode(), response.status_code

    def get_feature_types(
        self, workspace_name: str, datastore_name: str
    ) -> tuple[FeatureTypes | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.featuretypes(workspace_name, datastore_name)
        )
        return self.deserialize_response(response, FeatureTypes)

    def get_feature_type(
        self, workspace_name: str, datastore_name: str, feature_type_name: str
    ) -> tuple[FeatureType | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.featuretype(
                workspace_name, datastore_name, feature_type_name
            )
        )
        return self.deserialize_response(response, FeatureType)

    def get_coverages(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[Coverages | str, int]:
        """Get all coverages for a given workspace and coverage store"""
        response: Response = self.rest_client.get(
            path=self.rest_endpoints.coverages(workspace_name, coveragestore_name),
            params={"list": "all"},
        )
        return self.deserialize_response(response, Coverages)

    def get_coverage(
        self, workspace_name: str, coveragestore_name: str, coverage_name: str
    ) -> tuple[Coverage | str, int]:
        """Get a single coverage for a given workspace, coverage store, and coverage name"""
        response: Response = self.rest_client.get(
            self.rest_endpoints.coverage(
                workspace_name, coveragestore_name, coverage_name
            )
        )
        return self.deserialize_response(response, Coverage)

    def create_coverage(self, coverage: Coverage) -> tuple[str, int]:
        """
        Publish a coverage layer
        """
        response: Response = self.rest_client.post(
            self.rest_endpoints.coverages(coverage.workspace_name, coverage.store_name),
            json=coverage.post_payload(),
        )
        return response.content.decode(), response.status_code

    def get_coverage_store(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[CoverageStore | str, int]:
        """Get a coverage store for a given workspace and coverage store name"""
        response: Response = self.rest_client.get(
            self.rest_endpoints.coveragestore(workspace_name, coveragestore_name)
        )
        return self.deserialize_response(response, CoverageStore)

    def create_coverage_store(self, coverage_store: CoverageStore) -> tuple[str, int]:
        """
        Create a coverage store from a coverage store definition
        """
        response: Response = self.rest_client.post(
            self.rest_endpoints.coveragestores(coverage_store.workspace.name),
            json=coverage_store.post_payload(),
        )
        return response.content.decode(), response.status_code

    def create_imagemosaic_store_from_directory(
        self, workspace_name: str, coveragestore_name: str, directory_path: str
    ) -> tuple[str, int]:
        """
        Create an ImageMosaic coverage store from a directory on the server
        """
        response: Response = self.rest_client.put(
            self.rest_endpoints.coveragestore(
                workspace_name, coveragestore_name, "external", "imagemosaic"
            ),
            data=directory_path,
            headers={"Content-Type": "text/plain", "Accept": "application/json"},
        )
        coverage_store, status_code = self.deserialize_response(response, CoverageStore)
        if isinstance(coverage_store, str):
            return coverage_store, status_code
        else:
            return coverage_store.name, status_code

    def create_imagemosaic_store_from_properties_zip(
        self, workspace_name: str, coveragestore_name: str, properties_zip: bytes
    ) -> tuple[str, int]:
        """
        Create an empty ImageMosaic coverage store from a ZIP containing the
        configuration files indexer.properties and datastore.properties
        """
        response: Response = self.rest_client.put(
            self.rest_endpoints.coveragestore(
                workspace_name, coveragestore_name, "file", "imagemosaic"
            ),
            params={"configure": "none"},
            data=properties_zip,
            headers={"Content-Type": "application/zip", "Accept": "application/json"},
        )
        return response.content.decode(), response.status_code

    def publish_granule_to_coverage_store(
        self,
        workspace_name: str,
        coveragestore_name: str,
        method: str,
        granule_path: str,
    ) -> tuple[str, int]:
        response: Response = self.rest_client.post(
            self.rest_endpoints.coveragestore(
                workspace_name, coveragestore_name, method, "imagemosaic"
            ),
            data=granule_path,
            headers={"Content-Type": "text/plain", "Accept": "application/json"},
        )
        return response.content.decode(), response.status_code

    def harvest_granules_to_coverage_store(
        self, workspace_name: str, coveragestore_name: str, directory_path: str
    ) -> tuple[str, int]:
        response: Response = self.rest_client.post(
            self.rest_endpoints.coveragestore(
                workspace_name, coveragestore_name, "external", "imagemosaic"
            ),
            data=directory_path,
            headers={"Content-Type": "text/plain", "Accept": "application/json"},
        )
        return response.content.decode(), response.status_code

    def delete_coverage_store(
        self, workspace_name: str, coveragestore_name: str
    ) -> tuple[str, int]:
        """Delete a coverage store recursively"""
        path = self.rest_endpoints.coveragestore(workspace_name, coveragestore_name)
        params: dict[str, str] = {"recurse": "true"}
        response: Response = self.rest_client.delete(path, params=params)
        return response.content.decode(), response.status_code

    def create_feature_type(self, feature_type: FeatureType) -> tuple[str, int]:
        path: str = self.rest_endpoints.featuretypes(
            feature_type.workspace_name, feature_type.store_name
        )
        resource_path: str = self.rest_endpoints.featuretype(
            feature_type.workspace_name, feature_type.store_name, feature_type.name
        )
        if not self.resource_exists(resource_path):
            response: Response = self.rest_client.post(
                path,
                json=feature_type.post_payload(),
            )
        else:
            response = self.rest_client.put(
                resource_path,
                json=feature_type.put_payload(),
            )
        return response.content.decode(), response.status_code

    def delete_feature_type(
        self, workspace_name: str, datastore_name: str, layer_name: str
    ) -> tuple[str, int]:
        response: Response = self.rest_client.delete(
            self.rest_endpoints.featuretype(workspace_name, datastore_name, layer_name),
            params={"recurse": "true"},
        )
        return response.content.decode(), response.status_code

    def get_layer_groups(self, workspace_name: str) -> tuple[LayerGroups | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.layergroups(workspace_name)
        )
        return self.deserialize_response(response, LayerGroups)

    def get_layer_group(
        self, workspace_name: str, layer_group_name: str
    ) -> tuple[LayerGroup | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.layergroup(workspace_name, layer_group_name)
        )
        return self.deserialize_response(response, LayerGroup)

    def create_layer_group(
        self,
        layer_group_name: str,
        workspace_name: str,
        layer_group: LayerGroup,
    ) -> tuple[str, int]:
        if not self.resource_exists(
            self.rest_endpoints.layergroup(workspace_name, layer_group_name)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.layergroups(workspace_name),
                json=layer_group.post_payload(),
            )
        else:
            response = self.rest_client.put(
                self.rest_endpoints.layergroup(workspace_name, layer_group_name),
                json=layer_group.put_payload(),
            )
        return response.content.decode(), response.status_code

    def delete_layer_group(
        self, workspace_name: str, layer_group_name: str
    ) -> tuple[str, int]:
        response: Response = self.rest_client.delete(
            self.rest_endpoints.layergroup(workspace_name, layer_group_name)
        )
        return response.content.decode(), response.status_code

    def get_styles(self, workspace_name: str | None = None) -> tuple[Styles | str, int]:
        path = self.rest_endpoints.styles(workspace_name=workspace_name)
        response: Response = self.rest_client.get(path)
        return self.deserialize_response(response, Styles)

    def get_style_definition(
        self, style: str, workspace_name: str | None = None
    ) -> tuple[Style | str, int]:
        path = self.rest_endpoints.style(style, workspace_name, format="json")
        return self.deserialize_response(self.rest_client.get(path), Style)

    def create_style_definition(
        self,
        style_name: str,
        style: Style,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        # Use XML because JSON is not supported for style creation
        path = self.rest_endpoints.styles(workspace_name=workspace_name, format="xml")
        resource_path = self.rest_endpoints.style(
            workspace_name=workspace_name, style_name=style_name, format="xml"
        )
        data: bytes = style.xml_post_payload().encode()
        headers: dict[str, str] = {"Content-Type": "text/xml"}
        # Use "Accept" header otherwise GeoServer throws a 500 on GET when the resource exists
        if not self.resource_exists(
            resource_path, headers={"Accept": "application/json"}
        ):
            response: Response = self.rest_client.post(path, data=data, headers=headers)
        else:
            response = self.rest_client.put(resource_path, data=data, headers=headers)
        return response.content.decode(), response.status_code

    def get_style(
        self, style: str, workspace_name: str | None = None, format: str = "sld"
    ) -> tuple[bytes | str, int]:
        path = self.rest_endpoints.style(style, workspace_name, format=format)
        response: Response = self.rest_client.get(path)
        if not response.ok:
            return response.content.decode(), response.status_code
        return response.content, response.status_code

    def create_style(
        self,
        style_name: str,
        style: bytes,
        workspace_name: str | None = None,
        format: str = "sld",
    ) -> tuple[str, int]:
        resource_path = self.rest_endpoints.style(
            workspace_name=workspace_name, style_name=style_name, format=format
        )
        if format == "sld":
            headers = {"Content-Type": "application/vnd.ogc.sld+xml"}
        elif format == "zip":
            headers = {"Content-Type": "application/zip"}
        # Do not check for existence because GeoServer throws a 500 if the style definition exists and not
        # the SLD. Besides PUT is also supported on creation
        response: Response = self.rest_client.put(
            resource_path, data=style, headers=headers
        )
        return response.content.decode(), response.status_code

    def get_layer(
        self, workspace_name: str, layer_name: str
    ) -> tuple[Layer | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.workspace_layer(workspace_name, layer_name)
        )
        return self.deserialize_response(response, Layer)

    def update_layer(self, layer: Layer, workspace_name: str) -> tuple[str, int]:
        response: Response = self.rest_client.put(
            self.rest_endpoints.workspace_layer(workspace_name, layer.name),
            json=layer.put_payload(),
        )
        return response.content.decode(), response.status_code

    def create_user(
        self, user: str, password: str, enabled: bool = True
    ) -> tuple[str, int]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        payload: dict[str, dict[str, Any]] = {
            "user": {
                "userName": user,
                "password": password,
                "enabled": enabled,
            }
        }
        response: Response = self.rest_client.post(
            self.rest_endpoints.users(), json=payload, headers=headers
        )
        return response.content.decode(), response.status_code

    def update_user(
        self, user: str, password: str | None = None, enabled: bool | None = None
    ) -> tuple[str, int]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        payload: dict[str, dict[str, Any]] = {"user": {}}
        if password:
            payload["user"]["password"] = password
        if enabled is not None:
            payload["user"]["enabled"] = enabled
        response: Response = self.rest_client.post(
            self.rest_endpoints.user(user), json=payload, headers=headers
        )
        return response.content.decode(), response.status_code

    def delete_user(self, user: str) -> tuple[str, int]:
        response: Response = self.rest_client.delete(self.rest_endpoints.user(user))
        return response.content.decode(), response.status_code

    def create_role(self, role_name: str) -> tuple[str, int]:
        response: Response = self.rest_client.post(self.rest_endpoints.role(role_name))
        return response.content.decode(), response.status_code

    def delete_role(self, role_name: str) -> tuple[str, int]:
        response: Response = self.rest_client.delete(
            self.rest_endpoints.role(role_name)
        )
        return response.content.decode(), response.status_code

    def create_role_if_not_exists(self, role_name: str) -> tuple[str, int]:
        if self.role_exists(role_name):
            return "", 200
        return self.create_role(role_name)

    def role_exists(self, role_name: str) -> bool:
        response: Response = self.rest_client.get(
            self.rest_endpoints.roles(), headers={"Accept": "application/json"}
        )
        roles = response.json().get("roles", [])
        return role_name in roles

    def get_user_roles(self, user: str) -> tuple[list[str] | str, int]:
        response: Response = self.rest_client.get(self.rest_endpoints.user_roles(user))
        try:
            content = response.json().get("roles", [])
        except JSONDecodeError:
            content = response.content.decode()
        return content, response.status_code

    def assign_role_to_user(self, user: str, role: str) -> tuple[str, int]:
        response: Response = self.rest_client.post(
            self.rest_endpoints.role_user(role, user)
        )
        return response.content.decode(), response.status_code

    def remove_role_from_user(self, user: str, role: str) -> tuple[str, int]:
        response: Response = self.rest_client.delete(
            self.rest_endpoints.role_user(role, user)
        )
        return response.content.decode(), response.status_code

    def create_acl_admin_rule(
        self,
        priority: int = 0,
        access: str = "ADMIN",
        role: str | None = None,
        user: str | None = None,
        workspace_name: str | None = None,
    ) -> tuple[dict | str, int]:
        response: Response = self.rest_client.post(
            self.acl_endpoints.adminrules(),
            json={
                "priority": priority,
                "access": access,
                "role": role,
                "user": user,
                "workspace": workspace_name,
            },
        )
        try:
            content = response.json()
        except JSONDecodeError:
            content = response.content.decode()
        return content, response.status_code

    def delete_acl_admin_rule(self, id: str) -> tuple[str, int]:
        response: Response = self.rest_client.delete(self.acl_endpoints.adminrule(id))
        return response.content.decode(), response.status_code

    def delete_all_acl_admin_rules(self) -> tuple[str, int]:
        response: Response = self.rest_client.delete(self.acl_endpoints.adminrules())
        return response.content.decode(), response.status_code

    def get_acl_rules(self) -> tuple[dict[str, Any] | str, int]:
        response: Response = self.rest_client.get(self.acl_endpoints.rules())
        try:
            content = response.json()
        except JSONDecodeError:
            content = response.content.decode()
        return content, response.status_code

    def create_acl_rules_for_requests(
        self,
        requests: list[str],
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        service: str | None = None,
        workspace_name: str | None = None,
    ) -> list[tuple[dict | str, int]]:
        responses = []
        for request in requests:
            responses.append(
                self.create_acl_rule(
                    priority=priority,
                    access=access,
                    role=role,
                    request=request,
                    service=service,
                    workspace_name=workspace_name,
                )
            )
        return responses

    def create_acl_rule(
        self,
        priority: int = 0,
        access: str = "DENY",
        role: str | None = None,
        user: str | None = None,
        service: str | None = None,
        request: str | None = None,
        workspace_name: str | None = None,
    ) -> tuple[dict[str, Any] | str, int]:
        json = {"priority": priority, "access": access}
        if role:
            json["role"] = role
        if user:
            json["user"] = user
        if service:
            json["service"] = service
        if request:
            json["request"] = request
        if workspace_name:
            json["workspace"] = workspace_name
        response: Response = self.rest_client.post(
            self.acl_endpoints.rules(), json=json
        )
        try:
            content = response.json()
        except JSONDecodeError:
            content = response.content.decode()
        return content, response.status_code

    def delete_all_acl_rules(self) -> tuple[str, int]:
        response: Response = self.rest_client.delete(self.acl_endpoints.rules())
        return response.content.decode(), response.status_code

    def get_resource_directory(
        self, path: str, workspace_name: str | None = None
    ) -> tuple[ResourceDirectory | str, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.resource_directory(path, workspace_name),
            headers={"Accept": "application/json"},
        )
        return self.deserialize_response(response, ResourceDirectory)

    def get_resource(
        self, path: str, resource_name: str, workspace_name: str | None = None
    ) -> tuple[bytes, int]:
        response: Response = self.rest_client.get(
            self.rest_endpoints.resource(path, resource_name, workspace_name),
        )
        return response.content, response.status_code

    def put_resource(
        self,
        path: str,
        name: str,
        content_type: str,
        data: bytes,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        headers = {"Content-Type": content_type}
        response: Response = self.rest_client.put(
            path=self.rest_endpoints.resource(path, name, workspace_name),
            headers=headers,
            data=data,
        )
        return response.content.decode(), response.status_code

    @staticmethod
    def get_wmts_layer_bbox(
        url: str, layer_name: str
    ) -> tuple[float, float, float, float] | None:
        wmts = WebMapTileService(url)
        try:
            return wmts[layer_name].boundingBoxWGS84
        except (KeyError, AttributeError):
            return None

    def resource_exists(self, path: str, headers: dict[str, str] | None = None) -> bool:
        response: Response = self.rest_client.get(path, headers=headers)
        return response.status_code == 200

    @staticmethod
    def deserialize_response(
        response: Response, data_type: type[BaseModel]
    ) -> tuple[Any, int]:
        try:
            content = response.json()
        except JSONDecodeError:
            return response.content.decode(), response.status_code
        return data_type.from_get_response_payload(content), response.status_code

    class AclEndpoints:
        def __init__(self, base_url: str = "/acl") -> None:
            self.base_url: str = base_url

        def adminrules(self) -> str:
            return f"{self.base_url}/api/adminrules"

        def adminrule(self, id: str) -> str:
            return f"{self.base_url}/api/adminrules/id/{id}"

        def rules(self) -> str:
            return f"{self.base_url}/api/rules"

    class GwcEndpoints:
        def __init__(self, base_url: str = "/gwc/rest") -> None:
            self.base_url: str = base_url

        def reload(self) -> str:
            return f"{self.base_url}/reload"

        def layers(self, workspace_name: str) -> str:
            return f"{self.base_url}/layers.json"

        def layer(self, workspace_name: str, layer_name: str) -> str:
            return f"{self.base_url}/layers/{workspace_name}:{layer_name}.json"

        def gridsets(self) -> str:
            return f"{self.base_url}/gridsets.json"

        def gridset(self, epsg: int) -> str:
            return f"{self.base_url}/gridsets/EPSG:{str(epsg)}.xml"

    class RestEndpoints:
        def __init__(self, base_url: str = "/rest") -> None:
            self.base_url: str = base_url

        def styles(
            self, workspace_name: str | None = None, format: str = "json"
        ) -> str:
            if not workspace_name:
                url: str = f"{self.base_url}/styles"
            else:
                url = f"{self.base_url}/workspaces/{workspace_name}/styles"
            if format == "json":
                return f"{url}.json"
            return url

        def style(
            self,
            style_name: str,
            workspace_name: str | None = None,
            format: str = "json",
        ) -> str:
            if not workspace_name:
                url: str = f"{self.base_url}/styles/{style_name}"
            else:
                url = f"{self.base_url}/workspaces/{workspace_name}/styles/{style_name}"
            if format in ("json", "sld"):
                return f"{url}.{format}"
            return url

        def workspaces(self) -> str:
            return f"{self.base_url}/workspaces.json"

        def workspace(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}.json"

        def workspace_layer(self, workspace_name: str, layer_name: str) -> str:
            return f"{self.base_url}/layers/{workspace_name}:{layer_name}.json"

        def workspace_wms_settings(self, workspace_name: str) -> str:
            return f"{self.base_url}/services/wms/workspaces/{workspace_name}/settings.json"

        def workspace_wfs_settings(self, workspace_name: str) -> str:
            return f"{self.base_url}/services/wfs/workspaces/{workspace_name}/settings.json"

        def datastores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores.json"

        def datastore(self, workspace_name: str, datastore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores/{datastore_name}.json"

        def featuretypes(self, workspace_name: str, datastore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores/{datastore_name}/featuretypes.json"

        def featuretype(
            self, workspace_name: str, datastore_name: str, featuretype_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/datastores/{datastore_name}/featuretypes/{featuretype_name}.json"

        def layergroup(self, workspace_name: str, layergroup_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/layergroups/{layergroup_name}.json"

        def layergroups(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/layergroups.json"

        def coveragestores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores.json"

        def coveragestore(
            self,
            workspace_name: str,
            coveragestore_name: str,
            method: str | None = None,
            store_type: str | None = None,
        ) -> str:
            if method is None and store_type is None:
                return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}.json"
            else:
                return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/{method}.{store_type}"

        def coverages(self, workspace_name: str, coveragestore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages.json"

        def coverage(
            self, workspace_name: str, coveragestore_name: str, coverage_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}/coverages/{coverage_name}.json"

        def wmsstores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmsstores.json"

        def wmsstore(self, workspace_name: str, wmsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmsstores/{wmsstore_name}.json"

        def wmtsstores(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores.json"

        def wmslayers(self, workspace_name: str, wmtsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmsstores/{wmtsstore_name}/wmslayers.json"

        def wmslayer(
            self, workspace_name: str, wmtsstore_name: str, wmslayer_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmsstores/{wmtsstore_name}/wmslayers/{wmslayer_name}.json"

        def wmtsstore(self, workspace_name: str, wmtsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores/{wmtsstore_name}.json"

        def wmtslayers(self, workspace_name: str, wmtsstore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores/{wmtsstore_name}/layers.json"

        def wmtslayer(
            self, workspace_name: str, wmtsstore_name: str, wmtslayer_name: str
        ) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/wmtsstores/{wmtsstore_name}/layers/{wmtslayer_name}.json"

        def namespaces(self) -> str:
            return f"{self.base_url}/namespaces.json"

        def namespace(self, namespace_name: str) -> str:
            return f"{self.base_url}/namespaces/{namespace_name}.json"

        def users(self) -> str:
            return f"{self.base_url}/security/usergroup/users.json"

        def user(self, username: str) -> str:
            return f"{self.base_url}/security/usergroup/user/{username}.json"

        def roles(self) -> str:
            return f"{self.base_url}/security/roles.json"

        def user_roles(self, username: str) -> str:
            return f"{self.base_url}/security/roles/user/{username}.json"

        def role(self, role_name: str) -> str:
            return f"{self.base_url}/security/roles/role/{role_name}.json"

        def role_user(self, role_name: str, username: str) -> str:
            return (
                f"{self.base_url}/security/roles/role/{role_name}/user/{username}.json"
            )

        def resource_directory(
            self, relative_path: str, workspace_name: str | None = None
        ) -> str:
            if not workspace_name:
                return f"{self.base_url}/resource/{relative_path}"
            return (
                f"{self.base_url}/resource/workspaces/{workspace_name}/{relative_path}"
            )

        def resource(
            self,
            relative_path: str,
            resource_name: str,
            workspace_name: str | None = None,
        ) -> str:
            if not workspace_name:
                return f"{self.base_url}/resource/{relative_path}/{resource_name}"
            return f"{self.base_url}/resource/workspaces/{workspace_name}/{relative_path}/{resource_name}"
