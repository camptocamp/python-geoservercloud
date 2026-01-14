"""
Integration tests for cloud native data formats on private S3 buckets using AWS credentials chain.

These tests verify that GeoServer Cloud can access and serve cloud-optimized formats (COG, GeoParquet, PMTiles)
stored on private S3 buckets by using the AWS default credentials chain for authentication.

The credentials can be provided through:
- Environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- AWS credentials file: ~/.aws/credentials (mounted at /opt/app/home/.aws/credentials in containers)
- IAM roles (when running on AWS infrastructure)

In local development, credentials are typically mounted from compose/secrets/aws directory.
In CI/CD (GitHub Actions), credentials are configured from repository secrets.
"""

import pytest


@pytest.mark.aws_s3
def test_cog(geoserver_factory):
    """Test creating a COG coverage store and coverage on private S3 bucket"""
    workspace = "s3_private_cog"
    store_name = "land_shallow_topo_21600_NE_cog"
    coverage_name = "land_shallow_topo_21600_NE_cog"
    geoserver = geoserver_factory(workspace)

    # Create COG coverage store
    content, status = geoserver.create_coverage_store(
        workspace_name=workspace,
        coveragestore_name=store_name,
        type="GeoTIFF",
        url=f"cog://https://s3-us-east-1.amazonaws.com/geoserver-test-data-private/cog/land_shallow_topo/land_shallow_topo_21600_NE_cog.tif",
        metadata={"cogSettings": {"rangeReaderSettings": "S3"}},
    )
    assert status == 201
    assert content == store_name

    # Create coverage
    content, status = geoserver.create_coverage(
        workspace_name=workspace,
        coveragestore_name=store_name,
        coverage_name=coverage_name,
        native_name=store_name,
    )
    assert status == 201
    assert content == coverage_name

    # Verify the coverage was created - try listing coverages first
    content, status = geoserver.get_coverages(workspace, store_name)
    assert status == 200, f"Failed to get coverages: {status} - {content}"
    assert content[0].get("name") == store_name

    # Check specific coverage
    content, status = geoserver.get_coverage(workspace, store_name, coverage_name)
    assert status == 200, f"Failed to get coverage: {status} - {content}"

    # Verify coverage properties
    assert content.get("name") == coverage_name
    assert content.get("nativeName") == store_name
    assert content.get("enabled") is True

    # Test WMS GetMap request
    wms_response = geoserver.get_map(
        layers=[f"{workspace}:{coverage_name}"],
        bbox=(0, 0, 180, 90),
        size=(256, 256),
        srs="EPSG:4326",
        format="image/jpeg",
    )._response
    assert wms_response.status_code == 200
    assert wms_response.headers.get("content-type").startswith("image/jpeg")


@pytest.mark.aws_s3
def test_geoparquet(geoserver_factory):
    """Test creating a GeoParquet datastore on private S3 bucket"""
    workspace = "s3_private_geoparquet"
    datastore = "germany"
    geoserver = geoserver_factory(workspace)

    # Create GeoParquet datastore with S3 credentials chain
    content, status = geoserver.create_datastore(
        workspace_name=workspace,
        datastore_name=datastore,
        datastore_type="GeoParquet",
        connection_parameters={
            "dbtype": "geoparquet",
            "uri": "s3://geoserver-test-data-private/geoparquet/overture/singlefiles/germany/*",
            "namespace": workspace,
            "use_aws_credential_chain": True,
            "fetch size": 1000,
            "screenmap": True,
            "simplification": True,
        },
        description="GeoParquet datastore on private S3 bucket using AWS credentials chain",
    )
    assert status == 201, f"Failed to create datastore: {status} - {content}"
    assert content == datastore

    # Verify the datastore was created
    datastores, status = geoserver.get_datastores(workspace)
    assert status == 200
    assert datastore in [ds.get("name") for ds in datastores]

    # Get the datastore details
    datastore_info, status = geoserver.get_pg_datastore(workspace, datastore)
    assert status == 200
    assert datastore_info.get("name") == datastore
    assert datastore_info.get("type") == "GeoParquet"
    assert datastore_info.get("enabled") is True

    # Create feature type with explicit attributes since GeoParquet schema is known
    feature_type = "addresses"
    attributes = {
        "geometry": {"type": "Point", "required": False},
        "bbox": {"type": "string", "required": False},  # Struct type
        "country": {"type": "string", "required": False},
        "postcode": {"type": "string", "required": False},
        "street": {"type": "string", "required": False},
        "number": {"type": "string", "required": False},
        "unit": {"type": "string", "required": False},
        "postal_city": {"type": "string", "required": False},
        "version": {"type": "integer", "required": False},
        "theme": {"type": "string", "required": False},
        "type": {"type": "string", "required": False},
    }
    content, status = geoserver.create_feature_type(
        layer_name=feature_type,
        workspace_name=workspace,
        datastore_name=datastore,
        title="Germany Addresses from Overture Maps",
        abstract="Address points from Overture Maps for Germany, stored as GeoParquet on S3",
        epsg=4326,
        attributes=attributes,
    )
    assert status == 201, f"Failed to create feature type: {status} - {content}"

    # Verify the feature type was created
    feature_types, status = geoserver.get_feature_types(workspace, datastore)
    assert status == 200
    assert feature_type in [ft.get("name") for ft in feature_types]

    # Get the feature type details
    ft_info, status = geoserver.get_feature_type(workspace, datastore, feature_type)
    assert status == 200
    assert ft_info.get("name") == feature_type
    assert ft_info.get("enabled") is True

    # Test WFS GetFeature request (limit to 10 features for faster test)
    feature_collection = geoserver.get_feature(workspace, feature_type, max_feature=10)
    assert isinstance(feature_collection, dict)
    assert isinstance(feature_collection.get("features"), list)
    assert len(feature_collection.get("features", [])) > 0

    # Verify feature has expected properties
    feature = feature_collection["features"][0]
    properties = feature.get("properties")
    assert "geometry" in feature or "geometry" in properties
    # Check for some expected GeoParquet attributes
    assert any(
        key in properties for key in ["country", "street", "postcode", "postal_city"]
    )


@pytest.mark.aws_s3
def test_pmtiles(geoserver_factory):
    """Test creating a PMTiles datastore on private S3 bucket"""
    workspace = "s3_private_pmtiles"
    datastore = "europe"
    geoserver = geoserver_factory(workspace)

    # Create PMTiles datastore with S3 credentials chain
    content, status = geoserver.create_datastore(
        workspace_name=workspace,
        datastore_name=datastore,
        datastore_type="PMTiles",
        connection_parameters={
            "pmtiles": "s3://geoserver-test-data-private/pmtiles/shortbread/europe.pmtiles",
            "namespace": workspace,
            "io.tileverse.rangereader.s3.use-default-credentials-provider": True,
            "io.tileverse.rangereader.caching.enabled": True,
            "io.tileverse.rangereader.caching.blockaligned": True,
        },
        description="PMTiles datastore on private S3 bucket using AWS credentials chain",
    )
    assert status == 201, f"Failed to create datastore: {status} - {content}"
    assert content == datastore

    # Verify the datastore was created
    datastores, status = geoserver.get_datastores(workspace)
    assert status == 200
    assert datastore in [ds.get("name") for ds in datastores]

    # Get the datastore details
    datastore_info, status = geoserver.get_pg_datastore(workspace, datastore)
    assert status == 200
    assert datastore_info.get("name") == datastore
    assert datastore_info.get("type") == "PMTiles"
    assert datastore_info.get("enabled") is True

    # Create feature type with explicit attributes for PMTiles boundaries layer
    # Using EPSG:3857 (Web Mercator) - supported via monkey-patch at top of file
    feature_type = "boundaries"
    attributes = {
        "the_geom": {
            "type": "MultiPolygon",
            "required": False,
        },  # Boundaries are typically MultiPolygons
        "admin_level": {"type": "double", "required": False},
        "disputed": {"type": "boolean", "required": False},
        "maritime": {"type": "boolean", "required": False},
    }
    content, status = geoserver.create_feature_type(
        layer_name=feature_type,
        workspace_name=workspace,
        datastore_name=datastore,
        title="Boundaries from Shortbread Europe PMTiles",
        abstract="Administrative boundaries from Shortbread schema, stored as PMTiles on S3",
        epsg=3857,  # PMTiles uses Web Mercator (EPSG:3857)
        attributes=attributes,
    )
    assert status == 201, f"Failed to create feature type: {status} - {content}"

    # Verify the feature type was created
    feature_types, status = geoserver.get_feature_types(workspace, datastore)
    assert status == 200
    assert feature_type in [ft.get("name") for ft in feature_types]

    # Get the feature type details
    ft_info, status = geoserver.get_feature_type(workspace, datastore, feature_type)
    assert status == 200
    assert ft_info.get("name") == feature_type
    assert ft_info.get("enabled") is True
    assert ft_info.get("srs") == "EPSG:3857"

    # Test WFS GetFeature request (limit to 10 features for faster test)
    feature_collection = geoserver.get_feature(workspace, feature_type, max_feature=10)
    assert isinstance(feature_collection, dict)
    assert isinstance(feature_collection.get("features"), list)
    assert len(feature_collection.get("features", [])) > 0

    # Verify feature has expected properties
    feature = feature_collection["features"][0]
    properties = feature.get("properties")
    assert "geometry" in feature or "the_geom" in properties
    # Check for some expected PMTiles attributes
    assert any(key in properties for key in ["admin_level", "disputed", "maritime"])
