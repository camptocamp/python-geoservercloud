# GeoServer acceptance test suite

## Installation

The instructions below use `pip`, but it's also possible to use Poetry.

### From PyPI

We recommend working in a dedicated Python virtual environment.
To create and activate it (on Linux):

```shell
python -m venv .venv
source .venv/bin/activate
```

Install the lib:

```shell
pip install geoservercloud
```

### From local repository in development mode

```shell
git clone git@github.com:camptocamp/python-geoservercloud
cd python-geoservercloud/geoserver_acceptance_tests
python -m venv .venv
source .venv/bin/activate
pip install -e ..
```

## Prerequisites

- a GeoServer instance is running and accessible with an admin user
- a test Postgres DB with the PostGIS extension is accessible
- the ImageMosaic sample data is mounted in GeoServer at `/opt/geoserver_data/sampledata`
- Internet access (from GeoServer)

The ImageMosaic sample data is provided as an archive at data/sampledata.tgz.
A script is provided to copy the sample data and is available in the venv once the package is installed:

```shell
copy-test-data /example/path/
```

And to directly extract the sample data to its destination:

```shell
extract-test-data /example/path/
```

## Configuration

See example configuration file `example.config.yaml`. Most values can be overridden at run time through environment variables:

| Environment Variable          | Description                                         | Config Override     |
| ----------------------------- | --------------------------------------------------- | ------------------- |
| `GEOSERVER_ACCEPTANCE_CONFIG` | Path to the config YAML file                        | (overrides default) |
| `GEOSERVER_URL`               | GeoServer base URL                                  | `server.url`        |
| `GEOSERVER_VERIFYTLS`         | Enable/disable TLS verification. Expects true/false | `server.verifytls`  |
| `GEOSERVER_USER`              | GeoServer admin username                            | `credentials.user`  |
| `GEOSERVER_PASSWORD`          | GeoServer admin password                            | `credentials.pass`  |
| `GEOSERVER_PG_HOST_DOCKER`    | PostgreSQL host from Docker container               | `db.pg_host.docker` |
| `GEOSERVER_PG_PORT_DOCKER`    | PostgreSQL port from Docker container               | `db.pg_port.docker` |
| `GEOSERVER_PG_HOST_LOCAL`     | PostgreSQL host from local host                     | `db.pg_host.local`  |
| `GEOSERVER_PG_PORT_LOCAL`     | PostgreSQL port from local host                     | `db.pg_port.local`  |
| `GEOSERVER_PG_DB`             | PostgreSQL database name                            | `db.pg_db`          |
| `GEOSERVER_PG_USER`           | PostgreSQL username                                 | `db.pg_user`        |
| `GEOSERVER_PG_PASSWORD`       | PostgreSQL password                                 | `db.pg_password`    |
| `GEOSERVER_PG_SCHEMA`         | PostgreSQL schema                                   | `db.pg_schema`      |

There are two separate settings for the DB host and port because typically GeoServer and the DB are run as a docker composition while the tests themselves are run from the host. Supported host platforms are Linux, MacOS (experimental) and Windows (experimental) - feedback and PRs are welcome.

## Usage

Run tests

```shell
pytest --pyargs geoserver_acceptance_tests.tests -v
```

The default path to the configuration file is `/opt/geoserver_acceptance/config.yaml`. To change it - for example to use a file in the current directory, use the environment variable `GEOSERVER_ACCEPTANCE_CONFIG`:

```shell
GEOSERVER_ACCEPTANCE_CONFIG=./config.yaml pytest --pyargs geoserver_acceptance_tests.tests -v
```

### Enabling and disabling tests

Certain kinds of tests can be enabled or disabled through environment variables:

| Environment Variable                  | Description                                                   | Default |
| ------------------------------------- | ------------------------------------------------------------- | ------- |
| `GEOSERVER_ACCEPTANCE_RUN_DB_TESTS`   | Enable/disable tests requiring DB access                      | `true`  |
| `GEOSERVER_ACCEPTANCE_RUN_SLOW_TESTS` | Enable/disable slow tests                                     | `false` |
| `GEOSERVER_ACCEPTANCE_RUN_COG_TESTS`  | Enable/disable COG tests                                      | `false` |
| `GEOSERVER_ACCEPTANCE_RUN_JNDI_TESTS` | Enable/disable tests requiring a JNDI resource (jdbc/postgis) | `false` |

### Run the example docker composition

An example docker composition is provided in order to illustrate the complete setup required to run the tests.
First, follow the steps described at [From local repository in development mode](#from-local-repository-in-development-mode).
Then run:

```shell
extract-test-data ./compose/geoserver_data/
UID=$(id -u) docker compose -f compose/example.compose.yaml up -d
export GEOSERVER_ACCEPTANCE_CONFIG=./example.config.yaml
export GEOSERVER_ACCEPTANCE_RUN_JNDI_TESTS=true
pytest --pyargs geoserver_acceptance_tests.tests -v
```

### Image comparison tests

Some tests use image comparison. If such a test fails, the generated image will be persisted in a temporary directory created by pytest (check the test logs for the exact location). The temporary directory location can be overridden with the environment variable `GEOSERVER_ACCEPTANCE_FAILED_TESTS_DIR`.

This allows for visual comparison with the expected images which can be found in `tests/resources`.
