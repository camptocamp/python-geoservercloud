from geoservercloud.models.s3blobstore import S3Blobstore


def test_s3blobstore_from_get_response_payload_full():
    mock_response = {
        "S3BlobStore": {
            "id": "test_blobstore",
            "bucket": "test_bucket",
            "maxConnections": 10,
            "awsAccessKey": "access_key",
            "awsSecretKey": "secret_key",
            "prefix": "tiles",
            "enabled": True,
            "default": False,
            "access": "PUBLIC",
            "useHTTPS": True,
            "proxyDomain": "domain",
            "proxyWorkstation": "workstation",
            "proxyHost": "proxy.example.com",
            "proxyPort": "8080",
            "proxyUsername": "proxy_user",
            "proxyPassword": "proxy_pass",
            "useGzip": True,
            "endpoint": "s3.example.com",
        }
    }

    blobstore = S3Blobstore.from_get_response_payload(mock_response)

    assert blobstore.id == "test_blobstore"
    assert blobstore.bucket == "test_bucket"
    assert blobstore.max_connections == 10
    assert blobstore.aws_access_key == "access_key"
    assert blobstore.aws_secret_key == "secret_key"
    assert blobstore.prefix == "tiles"
    assert blobstore.enabled is True
    assert blobstore.default is False
    assert blobstore.access == "PUBLIC"
    assert blobstore.use_https is True
    assert blobstore.proxy_domain == "domain"
    assert blobstore.proxy_workstation == "workstation"
    assert blobstore.proxy_host == "proxy.example.com"
    assert blobstore.proxy_port == "8080"
    assert blobstore.proxy_username == "proxy_user"
    assert blobstore.proxy_password == "proxy_pass"
    assert blobstore.use_gzip is True
    assert blobstore.endpoint == "s3.example.com"


def test_s3blobstore_from_get_response_payload_required_only():
    mock_response = {
        "S3BlobStore": {
            "id": "test_blobstore",
            "bucket": "test_bucket",
            "maxConnections": 10,
        }
    }

    blobstore = S3Blobstore.from_get_response_payload(mock_response)

    assert blobstore.id == "test_blobstore"
    assert blobstore.bucket == "test_bucket"
    assert blobstore.max_connections == 10
    assert blobstore.aws_access_key is None
    assert blobstore.aws_secret_key is None
    assert blobstore.prefix is None
    assert blobstore.enabled is None
    assert blobstore.default is None
    assert blobstore.access is None
    assert blobstore.use_https is None
    assert blobstore.proxy_domain is None
    assert blobstore.proxy_workstation is None
    assert blobstore.proxy_host is None
    assert blobstore.proxy_port is None
    assert blobstore.proxy_username is None
    assert blobstore.proxy_password is None
    assert blobstore.use_gzip is None
    assert blobstore.endpoint is None
