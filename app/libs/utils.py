from jinja2 import escape


def convert_tx_id(tx_id):
    """
    Converts the guid tx_id to string of 16 characters with a dash between every 4 characters
    :param tx_id: tx_id to be converted
    :return: String in the form of xxxx-xxxx-xxxx-xxxx
    """
    return (tx_id[:4] + "-" + tx_id[4:])[:19]


# Converts a dict into an object with the key names as property names
class ObjectFromDict:
    def __init__(self, properties):
        self.__dict__ = properties


def escape_value(value):
    if isinstance(value, list):
        return [
            escape(list_item) if list_item and isinstance(list_item, str) else list_item
            for list_item in value
        ]

    if isinstance(value, dict):
        return {
            key: escape(val) if isinstance(val, str) else val
            for key, val in value.items()
        }

    return escape(value) if isinstance(value, str) else value
