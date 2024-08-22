# python-geoservercloud

## Installation

From PyPI:

```shell
pip install geoservercloud
```

From git repository:

```shell
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
