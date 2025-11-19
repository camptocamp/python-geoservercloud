import datetime
import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Callable

import pytest
import sqlalchemy

from geoservercloud import GeoServerCloud

from ..config import load_config

# Default base directory for persisting failed test artifacts
BASE_PERSIST_DIR = (
    Path(os.getenv("GEOSERVER_ACCEPTANCE_FAILED_TESTS_DIR", tempfile.gettempdir()))
    / "failed_tests"
)


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def test_source_directory():
    return Path(__file__).parent


@pytest.fixture(scope="session")
def geoserver(config: dict) -> GeoServerCloud:
    return GeoServerCloud(
        url=config["server"]["url"],
        user=config["credentials"]["user"],
        password=config["credentials"]["pass"],
        verifytls=config["server"].get("verifytls", True),
    )


@pytest.fixture(scope="function")
def geoserver_factory(
    request: pytest.FixtureRequest, geoserver: GeoServerCloud
) -> Callable[..., GeoServerCloud]:
    """
    Factory fixture to create a GeoServerCloud instance with a dedicated workspace.
    Cleanup (workspace deletion) is handled automatically.
    """

    def _create(workspace_name):
        geoserver.create_workspace(workspace_name, set_default_workspace=False)
        geoserver.publish_workspace(workspace_name)

        # Register cleanup for this workspace
        request.addfinalizer(lambda: geoserver.delete_workspace(workspace_name))
        request.addfinalizer(lambda: geoserver.cleanup())
        return geoserver

    return _create


@pytest.fixture(scope="session", autouse=True)
def engine(config: dict) -> Generator[sqlalchemy.Engine, None, None]:
    """Fixture to connect to the test DB from the host running the tests."""
    host = config["db"]["pg_host"]["local"]
    port = config["db"]["pg_port"]["local"]
    user = config["db"]["pg_user"]
    password = config["db"]["pg_password"]
    database = config["db"]["pg_db"]
    yield sqlalchemy.create_engine(
        f"postgresql://{user}:{password}@{host}:{port}/{database}",
    )


@pytest.fixture(scope="session", autouse=True)
def db_session(
    engine: sqlalchemy.Engine,
) -> Generator[sqlalchemy.Connection, None, None]:
    """DB session to the test database from the host running the tests."""
    yield engine.connect()


@pytest.fixture
def tmp_path_persistent(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Generator[Path, None, None]:
    """Path to a temporary directory that is persisted if the test fails."""
    yield tmp_path

    if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BASE_PERSIST_DIR / f"{request.node.name}_{timestamp}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tmp_path, dest)
        print(f"\n[INFO] Temporary files saved to: {dest}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_configure(config):
    """Configure pytest with custom markers."""

    markers = [
        "db: mark test as requiring database access",
        "cog: mark test as related to COG ImageMosaic",
        "jndi: mark test as requiring JNDI resource (jdbc/postgis) for DB access",
        "slow: mark test as slow to skip or run conditionally",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def env_var_is_true(var_name: str, default: bool = False) -> bool:
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.lower() in ["1", "true", "yes"]


def pytest_collection_modifyitems(config, items):
    """Conditionally skip tests based on environment variables."""

    # Run DB tests (default: true)
    if not env_var_is_true("GEOSERVER_ACCEPTANCE_RUN_DB_TESTS", True):
        skip_db = pytest.mark.skip(
            reason="use env var GEOSERVER_ACCEPTANCE_RUN_DB_TESTS=true to run"
        )
        for item in items:
            if "db" in item.keywords:
                item.add_marker(skip_db)

    # Run slow tests (default: false)
    if not env_var_is_true("GEOSERVER_ACCEPTANCE_RUN_SLOW_TESTS", False):
        skip_slow = pytest.mark.skip(
            reason="use env var GEOSERVER_ACCEPTANCE_RUN_SLOW_TESTS=true to run"
        )
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    # Run COG tests (default: false)
    if not env_var_is_true("GEOSERVER_ACCEPTANCE_RUN_COG_TESTS", False):
        skip_cog = pytest.mark.skip(
            reason="use env var GEOSERVER_ACCEPTANCE_RUN_COG_TESTS=true to run"
        )
        for item in items:
            if "cog" in item.keywords:
                item.add_marker(skip_cog)

    # Run JNDI tests (default: false)
    if not env_var_is_true("GEOSERVER_ACCEPTANCE_RUN_JNDI_TESTS", False):
        skip_jndi = pytest.mark.skip(
            reason="use env var GEOSERVER_ACCEPTANCE_RUN_JNDI_TESTS=true to run"
        )
        for item in items:
            if "jndi" in item.keywords:
                item.add_marker(skip_jndi)
