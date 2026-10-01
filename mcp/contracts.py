"""Validate the JSON Schema keywords used by this server, without runtime dependencies."""

import math
import re
from datetime import datetime


class ContractError(ValueError):
    pass


def validate(value, schema, path="arguments"):
    """Closed subset for our owned schemas; not a general-purpose JSON Schema engine."""
    kinds = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "null": value is None,
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }
    expected = schema.get("type")
    if expected and not any(kinds.get(kind, False) for kind in (expected if isinstance(expected, list) else [expected])):
        raise ContractError(f"{path}: invalid type")
    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{path}: invalid constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{path}: invalid choice")
    if isinstance(value, dict):
        if set(schema.get("required", [])) - value.keys():
            raise ContractError(f"{path}: missing required fields")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key not in properties and additional is False:
                raise ContractError(f"{path}: unknown field")
            child = properties.get(key, additional if isinstance(additional, dict) else {})
            validate(item, child, f"{path}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", math.inf):
            raise ContractError(f"{path}: invalid array length")
        if schema.get("uniqueItems") and len({repr(item) for item in value}) != len(value):
            raise ContractError(f"{path}: duplicate items")
        for index, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{path}[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", math.inf):
            raise ContractError(f"{path}: invalid text length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ContractError(f"{path}: invalid text pattern")
        if schema.get("format") == "date-time":
            try:
                if datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
                    raise ValueError("missing timezone")
            except ValueError as exc:
                raise ContractError(f"{path}: invalid timestamp") from exc
    if kinds["number"]:
        if isinstance(value, float) and not math.isfinite(value):
            raise ContractError(f"{path}: non-finite number")
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ContractError(f"{path}: out of range")
    if "oneOf" in schema:
        matches = 0
        for option in schema["oneOf"]:
            try:
                validate(value, option, path)
                matches += 1
            except ContractError:
                pass
        if matches != 1:
            raise ContractError(f"{path}: expected exactly one alternative")
