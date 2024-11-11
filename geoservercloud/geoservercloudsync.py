from geoservercloud.models.resourcedirectory import ResourceDirectory
from geoservercloud.services import RestService


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
    ) -> None:
        self.src_url: str = src_url.strip("/")
        self.src_user: str = src_user
        self.src_password: str = src_password
        self.src_auth: tuple[str, str] = (src_user, src_password)
        self.src_instance: RestService = RestService(src_url, self.src_auth)
        self.dst_url: str = dst_url.strip("/")
        self.dst_user: str = dst_user
        self.dst_password: str = dst_password
        self.dst_auth: tuple[str, str] = (dst_user, dst_password)
        self.dst_instance: RestService = RestService(dst_url, self.dst_auth)

    def copy_workspace(
        self, workspace_name: str, deep_copy: bool = False
    ) -> tuple[str, int]:
        """
        Copy a workspace from the source to the destination GeoServer instance.
        If deep_copy is True, the copy includes the styles in the workspace (including images).
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
        return new_workspace, new_ws_status_code

    def copy_styles(
        self, workspace_name: str | None = None, include_images: bool = True
    ) -> tuple[str, int]:
        """
        Copy all styles in a workspace (if a workspace is provided) or all global styles
        """
        if include_images:
            content, status_code = self.copy_style_images(workspace_name)
            if self.not_ok(status_code):
                return content, status_code
        styles, status_code = self.src_instance.get_styles(workspace_name)
        if isinstance(styles, str):
            return styles, status_code
        for style in styles.aslist():
            content, status_code = self.copy_style(style, workspace_name)
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
        style, status_code = self.src_instance.get_style(style_name, workspace_name)
        if isinstance(style, str):
            return style, status_code
        return self.dst_instance.create_style(style_name, style, workspace_name)

    def copy_style_images(self, workspace_name: str | None = None) -> tuple[str, int]:
        """
        Copy all images in a workspace's style directory, or all global style images if no workspace is provided
        """
        resource_dir, status_code = self.src_instance.get_resource_directory(
            path="styles", workspace_name=workspace_name
        )
        if isinstance(resource_dir, str):
            return resource_dir, status_code
        for child in resource_dir.children:
            if child.is_image():
                content, status_code = self.copy_resource(
                    resource_dir="styles",
                    resource_name=child.name,
                    content_type=child.type,
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
