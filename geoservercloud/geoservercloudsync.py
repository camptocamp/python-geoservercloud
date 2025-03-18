import json
from argparse import ArgumentParser
from requests.exceptions import HTTPError

from geoservercloud.services import RestService
from geoservercloud.exceptions import WorkspaceMissing, DatastoreMissing, GsDetail
from geoservercloud.models.layer import Layer


class GeoServerCloudSync:
    """
    Facade class allowing synchronization of GeoServer resources between two GeoServer instances

    Attributes
    ----------
    src_url : str
        base GeoServer URL for source GeoServer instance
    src_user : str
        GeoServer username for source GeoServer instance
    src_password : str
        GeoServer password for source GeoServer instance
    dst_url : str
        base GeoServer URL for destination GeoServer instance
    dst_user : str
        GeoServer username for destination GeoServer instance
    dst_password : str
        GeoServer password for destination GeoServer instance
    """

    def __init__(
        self,
        src_url: str,
        src_user: str,
        src_password: str,
        dst_url: str,
        dst_user: str,
        dst_password: str,
        src_verifytls: bool = True,
        dst_verifytls: bool = True,
    ) -> None:
        self.src_url: str = src_url.strip("/")
        self.src_user: str = src_user
        self.src_password: str = src_password
        self.src_auth: tuple[str, str] = (src_user, src_password)
        self.src_instance: RestService = RestService(
            src_url, self.src_auth, src_verifytls
        )
        self.dst_url: str = dst_url.strip("/")
        self.dst_user: str = dst_user
        self.dst_password: str = dst_password
        self.dst_auth: tuple[str, str] = (dst_user, dst_password)
        self.dst_instance: RestService = RestService(
            dst_url, self.dst_auth, src_verifytls
        )

    def copy_workspace(
        self, workspace_name: str, deep_copy: bool = False
    ) -> tuple[str, int]:
        """
        Copy a workspace from the source to the destination GeoServer instance.
        If deep_copy is True, the copy includes the PostGIS datastores, the feature types in the datastores,
        the corresponding layers, the layer groups and the styles in the workspace (including images).
        """
        workspace, status_code = self.src_instance.get_workspace(workspace_name)
        if isinstance(workspace, str):
            return workspace, status_code
        new_workspace, new_ws_status_code = self.dst_instance.create_workspace(
            workspace
        )
        if self.not_ok(new_ws_status_code):
            return new_workspace, new_ws_status_code
        if deep_copy:
            content, status_code = self.copy_styles(workspace_name)
            if self.not_ok(status_code):
                return content, status_code
            content, status_code = self.copy_pg_datastores(
                workspace_name, deep_copy=True
            )
            if self.not_ok(status_code):
                return content, status_code
            content, status_code = self.copy_layer_groups(workspace_name)
            if self.not_ok(status_code):
                return content, status_code
        return new_workspace, new_ws_status_code

    def copy_pg_datastores(
        self, workspace_name: str, deep_copy: bool = False
    ) -> tuple[str, int]:
        """
        Copy all the datastores in given workspace.
        If deep_copy is True, copy all feature types and the corresponding layers in each datastore
        """
        datastores, status_code = self.src_instance.get_datastores(workspace_name)
        if isinstance(datastores, str):
            return datastores, status_code
        elif datastores.aslist() == []:
            return "", status_code
        for datastore_name in datastores.aslist():
            content, status_code = self.copy_pg_datastore(
                workspace_name, datastore_name, deep_copy=deep_copy
            )
            if self.not_ok(status_code):
                return content, status_code
        return content, status_code

    def copy_pg_datastore(
        self, workspace_name: str, datastore_name: str, deep_copy: bool = False
    ) -> tuple[str, int]:
        """
        Copy a datastore from source to destination GeoServer instance
        If deep_copy is True, copy all feature types and the corresponding layers
        """
        datastore, status_code = self.src_instance.get_pg_datastore(
            workspace_name, datastore_name
        )
        if isinstance(datastore, str):
            return datastore, status_code
        new_ds, new_ds_status_code = self.dst_instance.create_pg_datastore(
            workspace_name, datastore
        )
        if self.not_ok(new_ds_status_code):
            return new_ds, new_ds_status_code
        if deep_copy:
            self.copy_feature_types(workspace_name, datastore_name, copy_layers=True)
        return new_ds, new_ds_status_code

    def copy_feature_types(
        self, workspace_name: str, datastore_name: str, copy_layers: bool = False
    ) -> tuple[str, int]:
        """
        Copy all feature types in a datastore from source to destination GeoServer instance
        """
        feature_types, status_code = self.src_instance.get_feature_types(
            workspace_name, datastore_name
        )
        if isinstance(feature_types, str):
            return feature_types, status_code
        elif feature_types.aslist() == []:
            return "", status_code
        for feature_type in feature_types.aslist():
            content, status_code = self.copy_feature_type(
                workspace_name, datastore_name, feature_type["name"]
            )
            if self.not_ok(status_code):
                return content, status_code
            if copy_layers:
                content, status_code = self.copy_layer(
                    workspace_name, feature_type["name"]
                )
                if self.not_ok(status_code):
                    return content, status_code
        return content, status_code

    def copy_feature_type(
        self, workspace_name: str, datastore_name: str, feature_type_name: str
    ) -> tuple[str, int]:
        """
        Copy a feature type from source to destination GeoServer instance
        """
        feature_type, status_code = self.src_instance.get_feature_type(
            workspace_name, datastore_name, feature_type_name
        )
        if isinstance(feature_type, str):
            return feature_type, status_code
        return self.dst_instance.create_feature_type(feature_type)

    def copy_layer(
        self, workspace_name: str, feature_type_name: str
    ) -> tuple[str, int]:
        """
        Copy a layer from source to destination GeoServer instance
        """
        layer, status_code = self.src_instance.get_layer(
            workspace_name, feature_type_name
        )
        resource, status_code = self.src_instance.get_resource_from_layer(layer)
        layer_string = json.dumps(layer.asdict())
        dst_layer = Layer.from_get_response_payload({
            "layer": json.loads(layer_string.replace(self.src_instance.url, self.dst_instance.url))
        })

        xml_resource_route = self.src_instance.get_resource_route_from_layer(layer)
        try:
            self.dst_instance.create_layer_resource(resource, xml_resource_route)
        except HTTPError:
            dst_resource = resource.decode().replace(self.src_instance.url, self.dst_instance.url)
            store = json.loads(dst_resource)["featureType"]["store"]
            if not self.dst_instance.check_href(store):
                raise DatastoreMissing(404, GsDetail(
                    f"Datastore {store['name']} not found",
                ))
            for ws_name, workspace in self.dst_instance.get_workspaces_from_store(store).items():
                if not self.dst_instance.check_href(workspace):
                    raise WorkspaceMissing(404, GsDetail(
                        f"Workspace {ws_name} not found",
                    ))

        return self.dst_instance.update_layer(dst_layer, workspace_name)

    def copy_layer_groups(self, workspace_name: str) -> tuple[str, int]:
        """
        Copy all layer groups in a workspace from source to destination GeoServer instance
        """
        layer_groups, status_code = self.src_instance.get_layer_groups(workspace_name)
        if isinstance(layer_groups, str):
            return layer_groups, status_code
        elif layer_groups.aslist() == []:
            return "", status_code
        for layer_group in layer_groups.aslist():
            content, status_code = self.copy_layer_group(
                workspace_name, layer_group["name"]
            )
            if self.not_ok(status_code):
                return content, status_code
        return content, status_code

    def copy_layer_group(
        self, workspace_name: str, layer_group_name: str
    ) -> tuple[str, int]:
        """
        Copy a layer group from source to destination GeoServer instance
        """
        layer_group, status_code = self.src_instance.get_layer_group(
            workspace_name, layer_group_name
        )
        if isinstance(layer_group, str):
            return layer_group, status_code
        return self.dst_instance.create_layer_group(
            layer_group_name, workspace_name, layer_group
        )

    def copy_styles(
        self, workspace_name: str | None = None, include_images: bool = True
    ) -> tuple[str, int]:
        """
        Copy all styles in a workspace (if a workspace is provided) or all global styles
        """
        styles, status_code = self.src_instance.get_styles(workspace_name)
        if isinstance(styles, str):
            return styles, status_code
        elif styles.aslist() == []:
            return "", status_code
        for style in styles.aslist():
            content, status_code = self.copy_style(style, workspace_name)
            if self.not_ok(status_code):
                return content, status_code
        if include_images:
            content, status_code = self.copy_style_images(workspace_name)
            if self.not_ok(status_code):
                return content, status_code
        return content, status_code

    def copy_style(
        self,
        style_name: str,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        """
        Copy a style from source to destination GeoServer instance
        """
        style_info, status_code = self.src_instance.get_style_info(
            style_name, workspace_name
        )
        if self.not_ok(status_code):
            return style_info, status_code
        style_definition_response, status_code = self.src_instance.get_style_definition(
            style_name, workspace_name, style_info.format
        )
        if self.not_ok(status_code):
            return style_definition_response.content, status_code
        try:
            content, status_code = self.dst_instance.create_style_info(style_name, style_info, workspace_name)
            if self.not_ok(status_code):
                return content, status_code
        except HTTPError:
            if not self.dst_instance.check_workspace_for_style(style_info):
                raise WorkspaceMissing(404, GsDetail(
                    f"Workspace {style_info.workspace_name} not found",
                ))

        return self.dst_instance.fill_style_definition(
            style_name,
            style_definition_response.content,
            style_info.format,
            style_definition_response.headers["content-type"],
            workspace_name
        )

    def copy_style_images(self, workspace_name: str | None = None) -> tuple[str, int]:
        """
        Copy all images in a workspace's style directory, or all global style images if no workspace is provided
        """
        resource_dir, status_code = self.src_instance.get_resource_directory(
            path="styles", workspace_name=workspace_name
        )
        if isinstance(resource_dir, str):
            return resource_dir, status_code
        images = [child for child in resource_dir.children if child.is_image()]
        if images == []:
            return "", status_code
        for image in images:
            content, status_code = self.copy_resource(
                resource_dir="styles",
                resource_name=image.name,
                content_type=image.type,
                workspace_name=workspace_name,
            )
        return content, status_code

    def copy_resource(
        self,
        resource_dir: str,
        resource_name: str,
        content_type: str,
        workspace_name: str | None = None,
    ) -> tuple[str, int]:
        """
        Copy a resource from source to destination GeoServer instance
        """
        resource, status_code = self.src_instance.get_resource(
            resource_dir, resource_name, workspace_name
        )
        if self.not_ok(status_code):
            return resource.decode(), status_code
        return self.dst_instance.put_resource(
            path=resource_dir,
            name=resource_name,
            workspace_name=workspace_name,
            content_type=content_type,
            data=resource,
        )

    @staticmethod
    def not_ok(http_status_code: int) -> bool:
        return http_status_code >= 400


def parse_args():
    parser = ArgumentParser(
        description="""
        Copy a workspace from a GeoServer instance to another, including PG datastores,
        layers, styles and style images.
        If using JNDI, the JNDI reference must exist in the destination GeoServer instance.
        """
    )
    parser.add_argument(
        "--src_url",
        help="URL of the source GeoServer instance",
        default="http://localhost:8080/geoserver",
    )
    parser.add_argument(
        "--src_user",
        default="admin",
        help="Admin user of the source GeoServer instance",
    )
    parser.add_argument(
        "--src_password",
        default="geoserver",
        help="Admin password of the source GeoServer instance",
    )
    parser.add_argument(
        "--dst_url",
        help="URL of the destination GeoServer instance",
        default="http://localhost:8080/geoserver",
    )
    parser.add_argument(
        "--dst_user",
        default="admin",
        help="Admin user of the destination GeoServer instance",
    )
    parser.add_argument(
        "--dst_password",
        default="geoserver",
        help="Admin password of the destination GeoServer instance",
    )
    parser.add_argument(
        "--workspace",
        help="Workspace to copy",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    geoserversync = GeoServerCloudSync(
        args.src_url,
        args.src_user,
        args.src_password,
        args.dst_url,
        args.dst_user,
        args.dst_password,
    )
    content, code = geoserversync.copy_workspace(args.workspace, deep_copy=True)
    print(code, content)
