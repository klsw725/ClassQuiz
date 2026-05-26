import json
from typing import cast


def participant_key(username: str, zone: str | None) -> str:
    return json.dumps([zone, username], ensure_ascii=False, separators=(",", ":"))


def parse_participant_key(key: str) -> tuple[str, str | None]:
    try:
        parsed = cast(object, json.loads(key))
    except json.JSONDecodeError:
        return key, None
    if isinstance(parsed, list):
        parsed_list = cast(list[object], parsed)
        if len(parsed_list) != 2:
            return key, None
        zone_value = parsed_list[0]
        username_value = parsed_list[1]
        if (zone_value is None or isinstance(zone_value, str)) and isinstance(username_value, str):
            return username_value, zone_value
    return key, None


def participant_display_data(key: str) -> dict[str, str]:
    username, zone = parse_participant_key(key)
    data = {"username": username}
    if zone is not None:
        data["zone"] = zone
    return data
