import os

import yaml

DEFAULT_CONFIG_PATH = "/opt/geoserver_acceptance/config.yaml"


def load_config():
    """Load test configuration from a YAML file.
    Environment variables can be used to override specific configuration values."""
    path = os.getenv("GEOSERVER_ACCEPTANCE_CONFIG", DEFAULT_CONFIG_PATH)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        config = yaml.safe_load(f)

    # Environment variables have precedence over configuration file
    override_url = os.getenv("GEOSERVER_URL")
    if override_url:
        config["server"]["url"] = override_url
    override_verifytls = os.getenv("GEOSERVER_VERIFYTLS")
    if override_verifytls is not None:
        config["server"]["verifytls"] = override_verifytls.lower() == "true"
    override_user = os.getenv("GEOSERVER_USER")
    if override_user:
        config["credentials"]["user"] = override_user
    override_pass = os.getenv("GEOSERVER_PASSWORD")
    if override_pass:
        config["credentials"]["pass"] = override_pass
    override_pg_host = os.getenv("GEOSERVER_PG_HOST_DOCKER")
    if override_pg_host:
        config["db"]["pg_host"]["docker"] = override_pg_host
    override_pg_port = os.getenv("GEOSERVER_PG_PORT_DOCKER")
    if override_pg_port:
        config["db"]["pg_port"]["docker"] = int(override_pg_port)
    override_pg_host = os.getenv("GEOSERVER_PG_HOST_LOCAL")
    if override_pg_host:
        config["db"]["pg_host"]["local"] = override_pg_host
    override_pg_port = os.getenv("GEOSERVER_PG_PORT_LOCAL")
    if override_pg_port:
        config["db"]["pg_port"]["local"] = int(override_pg_port)
    override_pg_db = os.getenv("GEOSERVER_PG_DB")
    if override_pg_db:
        config["db"]["pg_db"] = override_pg_db
    override_pg_user = os.getenv("GEOSERVER_PG_USER")
    if override_pg_user:
        config["db"]["pg_user"] = override_pg_user
    override_pg_password = os.getenv("GEOSERVER_PG_PASSWORD")
    if override_pg_password:
        config["db"]["pg_password"] = override_pg_password
    override_pg_schema = os.getenv("GEOSERVER_PG_SCHEMA")
    if override_pg_schema:
        config["db"]["pg_schema"] = override_pg_schema

    return config
