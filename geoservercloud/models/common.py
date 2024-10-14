import json
import logging
from typing import Any

log = logging.getLogger()


class KeyDollarListDict(dict):
    def __init__(
        self,
        input_list: list | None = None,
        input_dict: dict | None = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.key_prefix = "@key"
        self.value_prefix = "$"
        if input_list:
            self.deserialize(input_list)
        if input_dict:
            self.update(input_dict)
        log.debug(self)

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
    Class to handle internationalization of strings
    items like title, abstract, etc. that can be internationalized
    become a dictionary with the key being the language code
    and their key in the payload changes to internationalizedTitle, internationalizedAbstract, etc.
    """

    def __init__(self, keys: tuple[str, Any], value: str | dict) -> None:
        self._str_key = keys[0]
        self._i18n_key = keys[1]
        self._value = value
        if isinstance(value, str):
            self._payload = (self.str_key, self._value)
        elif isinstance(value, dict):
            self._payload = (self._i18n_key, self._value)  # type: ignore
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

    @property
    def payload_tuple(self):
        return self._payload

    def __repr__(self):
        return json.dumps({self._payload[0]: self._payload[1]}, indent=4)
