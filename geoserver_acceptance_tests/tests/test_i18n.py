from pathlib import Path
from pprint import pprint

import pytest
from requests.exceptions import JSONDecodeError
from sqlalchemy import Connection
from sqlalchemy.sql import text

from geoservercloud import GeoServerCloud
from geoservercloud.templates import Templates

from .utils import compare_images, write_actual_image

WORKSPACE = "test_i18n_workspace"


def international_title(default=True, de=True, fr=True, it=True, rm=True):
    title = {}
    if default:
        title["default"] = "Default title"
    if de:
        title["de"] = "Punkte"
    if fr:
        title["fr"] = "Points"
    if it:
        title["it"] = "Punti"
    if rm:
        title["rm"] = "Puncts"
    return title


def assert_legend(
    geoserver: GeoServerCloud, style: str, language: str | None, expected_label: str
):
    response = geoserver.get_legend_graphic(
        "i18n_legend",
        format="application/json",
        language=language,
        style=style,
        workspace_name=WORKSPACE,
    )
    try:
        label = response.json()["Legend"][0]["rules"][0]["title"]
        assert label == expected_label
    except (KeyError, JSONDecodeError):
        print(f"Invalid response for language '{language}:'\n{response.text}")
        assert False


@pytest.fixture(scope="module")
def resource_dir(test_source_directory: Path):
    return test_source_directory / "resources" / "i18n"


@pytest.fixture(scope="module")
def geoserver_i18n(geoserver: GeoServerCloud, config: dict):
    geoserver.create_workspace(WORKSPACE, set_default_workspace=True)
    geoserver.publish_workspace(WORKSPACE)
    geoserver.create_pg_datastore(
        workspace_name=WORKSPACE,
        datastore_name="i18n_datastore",
        pg_host=config["db"]["pg_host"]["docker"],
        pg_port=config["db"]["pg_port"]["docker"],
        pg_db=config["db"]["pg_db"],
        pg_user=config["db"]["pg_user"],
        pg_password=config["db"]["pg_password"],
        pg_schema=config["db"]["pg_schema"],
        set_default_datastore=True,
    )
    yield geoserver
    geoserver.delete_workspace(WORKSPACE)
    geoserver.cleanup()


@pytest.fixture(scope="module")
def geoserver_with_i18n_layers(geoserver_i18n: GeoServerCloud):

    # Create feature type with all languages
    layer1 = "layer_all_languages"
    title1 = international_title(default=True, de=True, fr=True, it=True, rm=True)
    geoserver_i18n.create_feature_type(
        layer1, title=title1, attributes=Templates.geom_point_attribute(), epsg=2056
    )

    # Create feature type without Rumantsch
    layer2 = "layer_no_rumantsch"
    title2 = international_title(default=True, de=True, fr=True, it=True, rm=False)
    geoserver_i18n.create_feature_type(
        layer2, title=title2, attributes=Templates.geom_point_attribute(), epsg=2056
    )

    # Create feature type without default language nor Rumantsch
    layer3 = "layer_no_default_no_rumantsch"
    title3 = international_title(default=False, de=True, fr=True, it=True, rm=False)
    geoserver_i18n.create_feature_type(
        layer3, title=title3, attributes=Templates.geom_point_attribute(), epsg=2056
    )

    yield geoserver_i18n


@pytest.fixture(scope="module")
def geoserver_default_locale_it(geoserver_with_i18n_layers: GeoServerCloud):
    geoserver_with_i18n_layers.set_default_locale_for_service(WORKSPACE, "it")
    yield geoserver_with_i18n_layers
    geoserver_with_i18n_layers.unset_default_locale_for_service(WORKSPACE)


@pytest.fixture(scope="module")
def geoserver_i18n_legend_layer(geoserver_i18n: GeoServerCloud, resource_dir: Path):
    geoserver_i18n.create_feature_type(
        "i18n_legend", attributes=Templates.geom_point_attribute(), epsg=2056
    )
    geoserver_i18n.create_style_from_file(
        "localized_with_default",
        str(resource_dir / "localized_with_default.sld"),
        workspace_name=WORKSPACE,
    )
    geoserver_i18n.create_style_from_file(
        "localized_no_default",
        str(resource_dir / "localized_no_default.sld"),
        workspace_name=WORKSPACE,
    )
    yield geoserver_i18n


@pytest.fixture(scope="module")
def geoserver_i18n_legend_layer_and_default_locale_it(
    geoserver_i18n_legend_layer: GeoServerCloud,
):
    geoserver_i18n_legend_layer.set_default_locale_for_service(WORKSPACE, "it")
    yield geoserver_i18n_legend_layer
    geoserver_i18n_legend_layer.unset_default_locale_for_service(WORKSPACE)


@pytest.fixture(scope="module")
def geoserver_i18n_label_layer(
    geoserver_i18n: GeoServerCloud,
    db_session: Connection,
    resource_dir: Path,
    config: dict,
):
    feature_type = "i18n_labels"
    table = f"{config['db']['pg_schema']}.{feature_type}"
    style = "localized_labels"
    file = str(resource_dir / f"{style}.sld")
    attributes = {
        "geom": {"type": "Point", "required": True},
        "label_default": {"type": "string", "required": False},
        "label_de": {"type": "string", "required": False},
        "label_fr": {"type": "string", "required": False},
    }
    geoserver_i18n.create_feature_type(feature_type, attributes=attributes, epsg=2056)
    geoserver_i18n.create_style_from_file(style, file, workspace_name=WORKSPACE)
    # Feature with labels in German, French and a default value
    db_session.execute(
        text(
            f"INSERT INTO {table} (geom, label_default, label_de, label_fr) VALUES "
            "(public.ST_SetSRID(public.ST_MakePoint(2600000, 1200000), 2056), 'Default label', 'Deutsches Label', 'Étiquette française')"
        )
    )
    # Feature with labels in German, French and no default value
    db_session.execute(
        text(
            f"INSERT INTO {table} (geom, label_de, label_fr) VALUES "
            "(public.ST_SetSRID(public.ST_MakePoint(2700000, 1300000), 2056), 'Deutsches Label', 'Étiquette française')"
        )
    )
    db_session.commit()
    yield geoserver_i18n


@pytest.fixture(scope="module")
def geoserver_i18n_label_default_locale_fr(geoserver_i18n_label_layer: GeoServerCloud):
    geoserver_i18n_label_layer.set_default_locale_for_service(WORKSPACE, "fr")
    yield geoserver_i18n_label_layer
    geoserver_i18n_label_layer.unset_default_locale_for_service(WORKSPACE)


@pytest.mark.parametrize(
    "language,expected_titles",
    [
        (
            "de",
            {
                "layer_all_languages": "Punkte",
                "layer_no_rumantsch": "Punkte",
                "layer_no_default_no_rumantsch": "Punkte",
            },
        ),
        (
            "de,fr",
            {
                "layer_all_languages": "Punkte",
                "layer_no_rumantsch": "Punkte",
                "layer_no_default_no_rumantsch": "Punkte",
            },
        ),
        (
            "fr,de",
            {
                "layer_all_languages": "Points",
                "layer_no_rumantsch": "Points",
                "layer_no_default_no_rumantsch": "Points",
            },
        ),
        (
            "rm",
            {
                "layer_all_languages": "Puncts",
                "layer_no_rumantsch": "Default title",
                "layer_no_default_no_rumantsch": "DID NOT FIND i18n CONTENT FOR THIS ELEMENT",
            },
        ),
        (
            "en",
            {},
        ),
        (
            None,
            {
                "layer_all_languages": "Default title",
                "layer_no_rumantsch": "Default title",
                "layer_no_default_no_rumantsch": "Punkte",
            },
        ),
        (
            "foobar",
            {},
        ),
    ],
)
@pytest.mark.db
def test_i18n_layers(
    geoserver_with_i18n_layers: GeoServerCloud,
    language: str | None,
    expected_titles: dict[str, str],
):
    capabilities = geoserver_with_i18n_layers.get_wms_layers(WORKSPACE, language)
    if type(capabilities) is list:
        for expected_layer, expected_title in expected_titles.items():
            actual_layer: dict = next(
                (layer for layer in capabilities if layer["Name"] == expected_layer), {}
            )
            assert actual_layer.get("Title") == expected_title
    else:
        pprint(capabilities)
        assert expected_titles == {}
        assert "ServiceExceptionReport" in capabilities


@pytest.mark.parametrize(
    "language,expected_titles",
    [
        (
            "de",
            {
                "layer_all_languages": "Punkte",
                "layer_no_rumantsch": "Punkte",
                "layer_no_default_no_rumantsch": "Punkte",
            },
        ),
        (
            "rm",
            {
                "layer_all_languages": "Puncts",
                "layer_no_rumantsch": "Default title",
                "layer_no_default_no_rumantsch": "DID NOT FIND i18n CONTENT FOR THIS ELEMENT",
            },
        ),
        (
            "en",
            {},
        ),
        (
            None,
            {
                "layer_all_languages": "Punti",
                "layer_no_rumantsch": "Punti",
                "layer_no_default_no_rumantsch": "Punti",
            },
        ),
    ],
)
@pytest.mark.db
def test_i18n_layers_default_locale(
    geoserver_default_locale_it: GeoServerCloud,
    language: str | None,
    expected_titles: dict[str, str],
):
    capabilities = geoserver_default_locale_it.get_wms_layers(WORKSPACE, language)
    if type(capabilities) is list:
        for expected_layer, expected_title in expected_titles.items():
            actual_layer: dict = next(
                (layer for layer in capabilities if layer["Name"] == expected_layer), {}
            )
            print(actual_layer["Name"])
            assert actual_layer.get("Title") == expected_title
    else:
        pprint(capabilities)
        assert expected_titles == {}
        assert "ServiceExceptionReport" in capabilities


@pytest.mark.parametrize(
    "language,expected_label",
    [
        ("en", "English"),
        ("de", "Deutsch"),
        ("fr", "Français"),
        ("it", "Italiano"),
        ("rm", "Default label"),
        (None, "Default label"),
        ("ru", "Default label"),
        ("foobar", "Default label"),
        ("it,fr,de", "Default label"),
    ],
)
@pytest.mark.db
def test_i18n_legend_with_default_value(
    geoserver_i18n_legend_layer: GeoServerCloud,
    language: str | None,
    expected_label: str,
):
    assert_legend(
        geoserver_i18n_legend_layer,
        "localized_with_default",
        language,
        expected_label,
    )


@pytest.mark.parametrize(
    "language,expected_label",
    [
        ("it", "Italiano"),
        ("rm", ""),
        (None, ""),
        ("ru", ""),
        ("foobar", ""),
        ("it,fr,de", ""),
    ],
)
@pytest.mark.db
def test_i18n_legend_no_default_value(
    geoserver_i18n_legend_layer: GeoServerCloud,
    language: str | None,
    expected_label: str,
):

    assert_legend(
        geoserver_i18n_legend_layer,
        "localized_no_default",
        language,
        expected_label,
    )


@pytest.mark.parametrize(
    "language,expected_label",
    [
        ("en", "English"),
        ("de", "Deutsch"),
        ("fr", "Français"),
        ("it", "Italiano"),
        ("rm", "Default label"),
        (None, "Default label"),
        ("ru", "Default label"),
        ("foobar", "Default label"),
        ("it,fr,de", "Default label"),
    ],
)
@pytest.mark.db
def test_i18n_legend_with_default_value_and_default_locale(
    geoserver_i18n_legend_layer_and_default_locale_it: GeoServerCloud,
    language: str | None,
    expected_label: str,
):
    assert_legend(
        geoserver_i18n_legend_layer_and_default_locale_it,
        "localized_with_default",
        language,
        expected_label,
    )


@pytest.mark.parametrize(
    "language,expected_label",
    [
        ("it", "Italiano"),
        ("rm", ""),
        (None, ""),
        ("ru", ""),
        ("foobar", ""),
        ("it,fr,de", ""),
    ],
)
@pytest.mark.db
def test_i18n_legend_no_default_value_default_locale(
    geoserver_i18n_legend_layer_and_default_locale_it: GeoServerCloud,
    language: str | None,
    expected_label: str,
):

    assert_legend(
        geoserver_i18n_legend_layer_and_default_locale_it,
        "localized_no_default",
        language,
        expected_label,
    )


@pytest.mark.parametrize("language", ["de", "fr", "it", None, ""])
@pytest.mark.db
def test_i18n_labels(
    geoserver_i18n_label_layer: GeoServerCloud,
    language: str | None,
    resource_dir: Path,
    tmp_path_persistent: Path,
):

    response = geoserver_i18n_label_layer.get_map(
        layers=["i18n_labels"],
        bbox=(2599999.5, 1199999.5, 2600000.5, 1200000.5),
        size=(300, 100),
        format="image/png",
        transparent=False,
        styles=["localized_labels"],
        language=language,
    )
    assert response is not None, f"GetMap request failed for language={language}"

    file_root = (
        Path("labels") / "no_default_locale" / "default_value" / f"language_{language}"
    )
    write_actual_image(tmp_path_persistent, file_root, response)
    compare_images(tmp_path_persistent, resource_dir, file_root)


@pytest.mark.parametrize("language", ["it", "", None])
@pytest.mark.db
def test_i18n_labels_no_default_value(
    geoserver_i18n_label_layer: GeoServerCloud,
    language: str | None,
    resource_dir: Path,
    tmp_path_persistent: Path,
):
    response = geoserver_i18n_label_layer.get_map(
        layers=["i18n_labels"],
        bbox=(2699999.5, 1299999.5, 2700000.5, 1300000.5),
        size=(300, 100),
        format="image/png",
        transparent=False,
        styles=["localized_labels"],
        language=language,
    )
    assert response is not None, f"GetMap request failed for language={language}"

    file_root = (
        Path("labels")
        / "no_default_locale"
        / "no_default_value"
        / f"language_{language}"
    )
    write_actual_image(tmp_path_persistent, file_root, response)
    compare_images(tmp_path_persistent, resource_dir, file_root)


@pytest.mark.parametrize("language", ["de", "fr", "it", None, ""])
@pytest.mark.db
def test_i18n_labels_default_locale(
    geoserver_i18n_label_default_locale_fr: GeoServerCloud,
    resource_dir: Path,
    tmp_path_persistent: Path,
    language: str | None,
):

    response = geoserver_i18n_label_default_locale_fr.get_map(
        layers=["i18n_labels"],
        bbox=(2599999.5, 1199999.5, 2600000.5, 1200000.5),
        size=(300, 100),
        format="image/png",
        transparent=False,
        styles=["localized_labels"],
        language=language,
    )
    assert response is not None, f"GetMap request failed for language={language}"

    file_root = (
        Path("labels") / "default_locale" / "default_value" / f"language_{language}"
    )
    write_actual_image(tmp_path_persistent, file_root, response)
    compare_images(tmp_path_persistent, resource_dir, file_root)


@pytest.mark.parametrize("language", ["it", "", None])
@pytest.mark.db
def test_i18n_labels_no_default_value_default_locale(
    geoserver_i18n_label_default_locale_fr: GeoServerCloud,
    resource_dir: Path,
    tmp_path_persistent: Path,
    language: str | None,
):

    response = geoserver_i18n_label_default_locale_fr.get_map(
        layers=["i18n_labels"],
        bbox=(2699999.5, 1299999.5, 2700000.5, 1300000.5),
        size=(300, 100),
        format="image/png",
        transparent=False,
        styles=["localized_labels"],
        language=language,
    )
    assert response is not None, f"GetMap request failed for language={language}"

    file_root = (
        Path("labels") / "default_locale" / "no_default_value" / f"language_{language}"
    )
    write_actual_image(tmp_path_persistent, file_root, response)
    compare_images(tmp_path_persistent, resource_dir, file_root)
