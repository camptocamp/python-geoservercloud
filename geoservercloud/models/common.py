import json
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BaseModel:
    @classmethod
    def from_get_response_payload(cls, content: dict):
        raise NotImplementedError


class EntityModel(BaseModel):
    def asdict(self) -> dict[str, Any]:
        raise NotImplementedError

    def post_payload(self) -> dict[str, Any]:
        raise NotImplementedError

    def put_payload(self) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def add_items_to_dict(content: dict, items: dict[str, Any]) -> dict[Any, Any]:
        for key, value in items.items():
            content = EntityModel.add_item_to_dict(content, key, value)
        return content

    @staticmethod
    def add_item_to_dict(content: dict, key: str, value: Any) -> dict[Any, Any]:
        if value is not None:
            content[key] = value
        return content


class ListModel(BaseModel, Generic[T]):
    """Base class for list-based models with configurable list and item names."""

    # These should be overridden in subclasses
    _list_key: str = ""  # e.g., "workspaces", "dataStores"
    _item_key: str = ""  # e.g., "workspace", "dataStore"

    def __init__(self, items: list[T] | None = None) -> None:
        self._items: list[T] = items or []

    def aslist(self) -> list[T]:
        """Return the list of items."""
        return self._items

    def find(self, name: str) -> T | None:
        """Find an item by name (assumes items are dicts with 'name' key)."""
        for item in self._items:
            if isinstance(item, dict) and item.get("name") == name:
                return item
        return None

    @classmethod
    def from_get_response_payload(cls, content: dict):
        """Create instance from API response payload."""
        if not cls._list_key or not cls._item_key:
            raise NotImplementedError("Subclasses must define _list_key and _item_key")

        data = content.get(cls._list_key)
        if not data:
            return cls()

        items = data[cls._item_key]
        return cls(items)

    def __repr__(self) -> str:
        """String representation of the list."""
        return json.dumps(self._items, indent=4)


class ReferencedObjectModel(BaseModel):
    def __init__(self, name: str, href: str | None = None):
        self.name: str = name
        self.href: str | None = href

    @classmethod
    def from_get_response_payload(cls, content: dict):
        cls.name = content["name"]
        cls.href = content["href"]

    def asdict(self) -> dict[str, str]:
        return EntityModel.add_item_to_dict({"name": self.name}, "href", self.href)


class KeyDollarListDict(dict):

    key_prefix: str = "@key"
    value_prefix: str = "$"

    def __init__(
        self,
        input_list: list | None = None,
        input_dict: dict | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        if input_list:
            self.deserialize(input_list)
        if input_dict:
            self.update(input_dict)

    def deserialize(self, input_list: list):
        for item in input_list:
            key = item[self.key_prefix]
            if self.value_prefix in item:
                value = item[self.value_prefix]
            else:
                value = None
            super().__setitem__(key, value)

    def serialize(self):
        return [
            {self.key_prefix: key, self.value_prefix: value}
            for key, value in self.items()
        ]

    def __repr__(self) -> str:
        return str(self.serialize())

    def __str__(self):
        return json.dumps(self.serialize())

    def update(self, other: dict):  # type: ignore
        for key, value in other.items():
            super().__setitem__(key, value)


class I18N:
    """
    Geoserver handles internationalization with 2 possible (mutually exclusive) keys in the rest payload:
    either:
    - [key: string]
    or
    - [internationalKey: dictionary]

    example:
    a) as key: string we get {"title": "Test Title"}
    b) as key: dict we get {"internationalTitle": {"en": "Test Title", "es": "Título de Prueba"}}

    This class gives a layer of abstraction to handle both cases.

    Usage:
    Call the class by adding both possible keys in a tuple and the value.

    Parameters:
    keys: tuple[str, str] example : ("title", "internationalTitle")
    value: str | dict example: "Test Title" | {"en": "Test Title", "es": "Título de Prueba"}

    Example:

    my_i18n = I18N(("title", "internationalTitle"), "Test Title")
    """

    def __init__(self, keys: tuple[str, Any], value: str | dict) -> None:
        self._str_key = keys[0]
        self._i18n_key = keys[1]
        self._value = value
        if isinstance(value, str):
            self._content = {self.str_key: self._value}
        elif isinstance(value, dict):
            self._content = {self._i18n_key: self._value}
        else:
            raise ValueError("Invalid value type")

    @property
    def str_key(self):
        return self._str_key

    @property
    def i18n_key(self):
        return self._i18n_key

    @property
    def value(self):
        return self._value

    def asdict(self):
        return self._content

    def __repr__(self):
        return json.dumps(self._content, indent=4)


class MetadataLink:
    def __init__(self, url: str, metadata_type="TC211", mime_type: str = "text/xml"):
        self.url: str = url
        self.metadata_type: str = metadata_type
        self.type: str = mime_type

    @classmethod
    def from_get_response_payload(cls, content: dict):
        return cls(
            url=content["content"],
            metadata_type=content["metadataType"],
            mime_type=content["type"],
        )

    def asdict(self) -> dict[str, str]:
        return {
            "content": self.url,
            "metadataType": self.metadata_type,
            "type": self.type,
        }
