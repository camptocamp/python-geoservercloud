# python-geoservercloud

## Documentation

https://camptocamp.github.io/python-geoservercloud/

## Installation

From PyPI:

```shell
pip install geoservercloud
```

From git repository:

```shell
git clone https://github.com/camptocamp/python-geoservercloud
cd python-geoservercloud
python3 -m venv .venv
source .venv/bin/activate
poetry install
```

## Quick start

```python
from geoservercloud import GeoServerCloud
geoserver = GeoServerCloud(
    url="http://localhost:9090/geoserver/cloud/",
    user="admin",
    password="geoserver",
)
geoserver.create_workspace("newworkspace")
```

## About

Lightweight Python client to interact with GeoServer Cloud REST API, GeoServer ACL and OGC services.
Intended use cases are listed below.

### Programmatic setup of a GeoServer catalog

For example, creating a workspace, connecting to a PostGIS datastore and publishing a PG layer:

```python
geoserver.create_workspace("example")
geoserver.create_pg_datastore(
    workspace_name="example",
    datastore_name="example_store",
    pg_host="localhost",
    pg_port=5432,
    pg_db="database",
    pg_user="user",
    pg_password="password"
)
geoserver.create_feature_type(
    layer_name="layer_example",
    workspace_name="example",
    datastore_name="example_store",
    title={
        "en":"Layer title",
        "fr": "Titre de la couche",
        "default": "Default title",
    },
)
```

### Testing

Automatic tests of GeoServer functionalities with `pytest`, for example before upgrading.
The example below tests the fallback mechanism for internationalized layer titles in the GetCapabilities document.

```python
@pytest.mark.parametrize(
    "language,expected_title",
    [
        (
            "en",
            "Layer title",
        ),
        (
            "fr",
            "Titre de la couche",
        ),
        (
            "de,en",
            "Layer title",
        ),
        (
            None,
            "Default title",
        ),
    ],
)
def test_i18n_layer_title(geoserver, language, expected_title):
    capabilities = geoserver.get_wms_layers(
        workspace="example",
        accept_languages=language,
    )
    layer = capabilities.get("Layer")
    assert layer.get("Title") == expected_title
```

### Syncing

Copying a workspace from one GeoServer instance to another, including PG datastores, layers, styles and style images.

#### In a Python console or script

```python
from geoservercloud import GeoServerCloudSync
geoserversync = GeoServerCloudSync(
    src_url="http://localhost:8080/geoserver",
    src_user="admin",
    src_password="geoserver",
    dst_url="http://localhost:9099/geoserver",
    dst_user="admin",
    dst_password="geoserver",
)
geoserversync.copy_workspace("workspace_name", deep_copy=True)
```

#### In a shell terminal or script

First install the package in your current virtual environment (see [Installation](#installation)), then run the script with:

```shell
copy-workspace --src_url "http://localhost:8080/geoserver" --src_user admin --src_password geoserver --dst_url "http://localhost:9099/geoserver" --dst_user admin --dst_password geoserver --workspace workspace_name
```
