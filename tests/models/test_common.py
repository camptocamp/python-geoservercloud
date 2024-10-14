import json

import pytest

from geoservercloud.models import (  # Adjust import based on your module location
    I18N,
    KeyDollarListDict,
)


# Test initialization with input_list (deserialization)
def test_keydollarlistdict_initialization_with_input_list():
    input_list = [{"@key": "host", "$": "localhost"}, {"@key": "port", "$": "5432"}]

    kdl_dict = KeyDollarListDict(input_list)

    assert kdl_dict["host"] == "localhost"
    assert kdl_dict["port"] == "5432"


# Test initialization without input_list
def test_keydollarlistdict_initialization_without_input_list():
    kdl_dict = KeyDollarListDict()

    assert len(kdl_dict) == 0  # Should be an empty dictionary


# Test deserialization of input_list
def test_keydollarlistdict_deserialization():
    input_list = [
        {"@key": "username", "$": "admin"},
        {"@key": "password", "$": "secret"},
    ]

    kdl_dict = KeyDollarListDict(input_list)

    assert kdl_dict["username"] == "admin"
    assert kdl_dict["password"] == "secret"


# Test serialization method
def test_keydollarlistdict_serialization():
    kdl_dict = KeyDollarListDict()
    kdl_dict["host"] = "localhost"
    kdl_dict["port"] = "5432"

    expected_output = [
        {"@key": "host", "$": "localhost"},
        {"@key": "port", "$": "5432"},
    ]

    assert kdl_dict.serialize() == expected_output


# Test __repr__ method
def test_keydollarlistdict_repr():
    kdl_dict = KeyDollarListDict([{"@key": "db", "$": "postgres"}])

    expected_repr = "[{'@key': 'db', '$': 'postgres'}]"

    assert repr(kdl_dict) == expected_repr


# Test __str__ method
def test_keydollarlistdict_str():
    kdl_dict = KeyDollarListDict([{"@key": "db", "$": "postgres"}])

    expected_str = json.dumps([{"@key": "db", "$": "postgres"}])

    assert str(kdl_dict) == expected_str


# Test initialization with a string value
def test_i18n_initialization_string():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"

    i18n_instance = I18N(keys, value)

    assert i18n_instance.str_key == "title"
    assert i18n_instance.i18n_key == "internationalizedTitle"
    assert i18n_instance.value == value
    assert i18n_instance._payload == ("title", value)


# Test initialization with a dictionary value (internationalized)
def test_i18n_initialization_dict():
    keys = ("abstract", "internationalizedAbstract")
    value = {"en": "Test Abstract", "fr": "Résumé Test"}

    i18n_instance = I18N(keys, value)

    assert i18n_instance.str_key == "abstract"
    assert i18n_instance.i18n_key == "internationalizedAbstract"
    assert i18n_instance.value == value
    assert i18n_instance._payload == ("internationalizedAbstract", value)


# Test invalid value type (neither string nor dictionary)
def test_i18n_invalid_value_type():
    keys = ("title", "internationalizedTitle")
    value = 123  # Invalid value type

    with pytest.raises(ValueError, match="Invalid value type"):
        I18N(keys, value)


# Test str_key property
def test_i18n_str_key_property():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"
    i18n_instance = I18N(keys, value)

    assert i18n_instance.str_key == "title"


# Test i18n_key property
def test_i18n_i18n_key_property():
    keys = ("abstract", "internationalizedAbstract")
    value = {"en": "Test Abstract", "fr": "Résumé Test"}
    i18n_instance = I18N(keys, value)

    assert i18n_instance.i18n_key == "internationalizedAbstract"


# Test value property
def test_i18n_value_property():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"
    i18n_instance = I18N(keys, value)

    assert i18n_instance.value == "Test Title"


def test_i18n_payload_tuple_property():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"
    i18n_instance = I18N(keys, value)

    assert i18n_instance.payload_tuple == ("title", "Test Title")


def test_i18n_repr():
    keys = ("title", "internationalizedTitle")
    value = "Test Title"
    i18n_instance = I18N(keys, value)

    assert repr(i18n_instance) == json.dumps({"title": "Test Title"}, indent=4)
