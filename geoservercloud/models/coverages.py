from geoservercloud.models.common import ListModel


class Coverages(ListModel[dict[str, str]]):
    _list_key = "coverages"
    _item_key = "coverage"

    @classmethod
    def from_get_response_payload(cls, content: dict):
        """
        Create a list of coverages from GET response payload.
        Sometimes the object structure is {"coverages": {"coverage": []}},
        sometimes it is {"list":{"string": []}}
        """
        if Coverages._list_key in content:
            return super().from_get_response_payload(content)
        elif "list" in content:
            names = content.get("list", {}).get("string", [])
            return cls([{"name": name} for name in names])
