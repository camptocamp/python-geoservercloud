import json

import pytest

from geoservercloud.models import I18N, KeyDollarListDict


def test_keydollarlistdict_initialization_with_input_list():
    input_list = [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]

    kdl_dict = KeyDollarListDict(input_list)

    assert kdl_dict["host"] == "localhost"
    assert kdl_dict["port"] == "5432"


def test_keydollarlistdict_initialization_without_input_list():
    kdl_dict = KeyDollarListDict()

    assert kdl_dict == {}


def test_keydollarlistdict_serialization():
    kdl_dict = KeyDollarListDict()
    kdl_dict["host"] = "localhost"
    kdl_dict["port"] = "5432"

    expected_output = [
        {"@key": "host", "$": "localhost"},
        {"@key": "port", "$": "5432"},
    ]

    assert kdl_dict.serialize() == expected_output


def test_keydollarlistdict_repr():
    kdl_dict = KeyDollarListDict([{"@key": "db", "$": "postgres"}])

    expected_repr = "[{'@key': 'db', '$': 'postgres'}]"

    assert repr(kdl_dict) == expected_repr


def test_keydollarlistdict_str():
    kdl_dict = KeyDollarListDict([{"@key": "db", "$": "postgres"}])

    expected_str = json.dumps([{"@key": "db", "$": "postgres"}])

    assert str(kdl_dict) == expected_str


def test_i18n_initialization_string():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"

    i18n_instance = I18N(keys, value)

    assert i18n_instance.str_key == "title"
    assert i18n_instance.i18n_key == "internationalizedTitle"
    assert i18n_instance.value == value
    assert i18n_instance.asdict() == {"title": value}


def test_i18n_initialization_dict():
    keys = ("abstract", "internationalizedAbstract")
    value = {"en": "Test Abstract", "fr": "Résumé Test"}

    i18n_instance = I18N(keys, value)

    assert i18n_instance.str_key == "abstract"
    assert i18n_instance.i18n_key == "internationalizedAbstract"
    assert i18n_instance.value == value
    assert i18n_instance.asdict() == {"internationalizedAbstract": value}


def test_i18n_invalid_value_type():
    keys = ("title", "internationalizedTitle")
    value = 123

    with pytest.raises(ValueError, match="Invalid value type"):
        I18N(keys, value)


def test_i18n_repr():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"
    i18n_instance = I18N(keys, value)

    assert repr(i18n_instance) == json.dumps({"title": "Test Title"}, indent=4)
