import json
from typing import Any

from geoservercloud.models.common import EntityModel


class S3Blobstore(EntityModel):
    def __init__(
        self,
        id: str,
        bucket: str,
        max_connections: int,
        aws_access_key: str | None = None,
        aws_secret_key: str | None = None,
        prefix: str | None = None,
        enabled: bool | None = None,
        default: bool | None = None,
        access: str | None = None,
        use_https: bool | None = None,
        proxy_domain: str | None = None,
        proxy_workstation: str | None = None,
        proxy_host: str | None = None,
        proxy_port: str | None = None,
        proxy_username: str | None = None,
        proxy_password: str | None = None,
        use_gzip: bool | None = None,
        endpoint: str | None = None,
    ):
        self.id = id
        self.bucket = bucket
        self.max_connections = max_connections
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.prefix = prefix
        self.enabled = enabled
        self.default = default
        self.access = access
        self.use_https = use_https
        self.proxy_domain = proxy_domain
        self.proxy_workstation = proxy_workstation
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.use_gzip = use_gzip
        self.endpoint = endpoint

    def asdict(self) -> dict[str, Any]:
        content: dict[str, Any] = {
            "id": self.id,
            "bucket": self.bucket,
            "maxConnections": self.max_connections,
        }
        optional_items: dict[str, Any] = {
            "awsAccessKey": self.aws_access_key,
            "awsSecretKey": self.aws_secret_key,
            "prefix": self.prefix,
            "enabled": self.enabled,
            "default": self.default,
            "access": self.access,
            "useHTTPS": self.use_https,
            "proxyDomain": self.proxy_domain,
            "proxyWorkstation": self.proxy_workstation,
            "proxyHost": self.proxy_host,
            "proxyPort": self.proxy_port,
            "proxyUsername": self.proxy_username,
            "proxyPassword": self.proxy_password,
            "useGzip": self.use_gzip,
            "endpoint": self.endpoint,
        }
        return EntityModel.add_items_to_dict(content, optional_items)

    def post_payload(self) -> dict[str, Any]:
        return {"S3BlobStore": self.asdict()}

    def put_payload(self) -> dict[str, Any]:
        return self.post_payload()

    @classmethod
    def from_get_response_payload(cls, content: dict):
        s3blobstore = content["S3BlobStore"]
        return cls(
            s3blobstore["id"],
            s3blobstore["bucket"],
            s3blobstore["maxConnections"],
            s3blobstore.get("awsAccessKey"),
            s3blobstore.get("awsSecretKey"),
            s3blobstore.get("prefix"),
            s3blobstore.get("enabled"),
            s3blobstore.get("default"),
            s3blobstore.get("access"),
            s3blobstore.get("useHTTPS"),
            s3blobstore.get("proxyDomain"),
            s3blobstore.get("proxyWorkstation"),
            s3blobstore.get("proxyHost"),
            s3blobstore.get("proxyPort"),
            s3blobstore.get("proxyUsername"),
            s3blobstore.get("proxyPassword"),
            s3blobstore.get("useGzip"),
            s3blobstore.get("endpoint"),
        )

    def __repr__(self) -> str:
        return json.dumps(self.put_payload(), indent=4)
