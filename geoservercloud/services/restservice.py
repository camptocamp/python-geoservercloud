from json import JSONDecodeError
from pathlib import Path
from typing import Any, Type

from requests import Response
from owslib.wmts import WebMapTileService

from geoservercloud import utils
from geoservercloud.models import (
    BaseModel,
    DataStores,
    PostGisDataStore,
    Workspace,
    Workspaces,
)
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

    def __init__(self, url: str, auth: tuple[str, str]) -> None:
        self.url: str = url
        self.auth: tuple[str, str] = auth
        self.rest_client = RestClient(url, auth)
        self.acl_endpoints = self.AclEndpoints()
        self.gwc_endpoints = self.GwcEndpoints()
        self.rest_endpoints = self.RestEndpoints()

    @staticmethod
    def get_wmts_layer_bbox(
        url: str, layer_name: str
    ) -> tuple[float, float, float, float] | None:
        wmts = WebMapTileService(url)
        try:
            return wmts[layer_name].boundingBoxWGS84
        except (KeyError, AttributeError):
            return None

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

    def publish_workspace(self, workspace: Workspace) -> tuple[str, int]:
        data: dict[str, dict[str, Any]] = Templates.workspace_wms(workspace.name)
        response: Response = self.rest_client.put(
            self.rest_endpoints.workspace_wms_settings(workspace.name), json=data
        )
        return response.content.decode(), response.status_code

    def set_default_locale_for_service(
        self, workspace: Workspace, locale: str | None
    ) -> None:
        data: dict[str, dict[str, Any]] = {
            "wms": {
                "defaultLocale": locale,
            }
        }
        self.rest_client.put(
            self.rest_endpoints.workspace_wms_settings(workspace.name), json=data
        )

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
            response: Response = self.rest_client.put(
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
            response: Response = self.rest_client.put(
                self.rest_endpoints.datastore(workspace_name, datastore.name),
                json=datastore.put_payload(),
            )
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
            response: Response = self.rest_client.put(
                self.rest_endpoints.wmtsstore(workspace_name, name), json=payload
            )
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

    def create_feature_type(
        self,
        layer: str,
        workspace_name: str,
        datastore: str,
        title: str | dict = "Default title",
        abstract: str | dict = "Default abstract",
        attributes: dict = Templates.geom_point_attribute(),
        epsg: int = 4326,
    ) -> tuple[str, int]:
        # TODO: use FeatureType.post_payload()
        payload: dict[str, dict[str, Any]] = Templates.feature_type(
            layer=layer,
            workspace=workspace_name,
            datastore=datastore,
            attributes=utils.convert_attributes(attributes),
            epsg=epsg,
        )
        if type(title) is dict:
            payload["featureType"]["internationalTitle"] = title
        else:
            payload["featureType"]["title"] = title
        if type(abstract) is dict:
            payload["featureType"]["internationalAbstract"] = abstract
        else:
            payload["featureType"]["abstract"] = abstract

        if not self.resource_exists(
            self.rest_endpoints.featuretype(workspace_name, datastore, layer)
        ):
            response: Response = self.rest_client.post(
                self.rest_endpoints.featuretypes(workspace_name, datastore),
                json=payload,
            )
        else:
            response: Response = self.rest_client.put(
                self.rest_endpoints.featuretype(workspace_name, datastore, layer),
                json=payload,
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
        """
        Get all roles assigned to a GeoServer user
        """
        response: Response = self.rest_client.get(self.rest_endpoints.user_roles(user))
        try:
            content = response.json().get("roles", [])
        except JSONDecodeError:
            content = response.content.decode()
        return content, response.status_code

    def resource_exists(self, path: str) -> bool:
        response: Response = self.rest_client.get(path)
        return response.status_code == 200

    def deserialize_response(
        self, response: Response, data_type: Type[BaseModel]
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

        def adminrule(self, id: int) -> str:
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

        def styles(self) -> str:
            return f"{self.base_url}/styles.json"

        def style(self, style_name: str) -> str:
            return f"{self.base_url}/styles/{style_name}.json"

        def workspaces(self) -> str:
            return f"{self.base_url}/workspaces.json"

        def workspace(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}.json"

        def workspace_styles(self, workspace_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/styles.json"

        def workspace_style(self, workspace_name: str, style_name: str) -> str:
            return (
                f"{self.base_url}/workspaces/{workspace_name}/styles/{style_name}.json"
            )

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

        def coveragestore(self, workspace_name: str, coveragestore_name: str) -> str:
            return f"{self.base_url}/workspaces/{workspace_name}/coveragestores/{coveragestore_name}.json"

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
