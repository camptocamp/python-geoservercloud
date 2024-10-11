import json

import pytest

from geoservercloud.models import (  # Adjust import based on your module location
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
