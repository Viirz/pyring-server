import re
import urllib.parse

def sanitize_input(data: dict) -> dict:
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Decode any URL-encoded characters
            decoded_value = urllib.parse.unquote(value)
            # Remove any characters that could be used for NoSQL injection
            sanitized_value = re.sub(r'[\$]', '', decoded_value)
            sanitized_data[key] = sanitized_value
        else:
            sanitized_data[key] = value
    return sanitized_data

def validate_request_data(request_data: dict, required_fields: dict):
    # Check for extra parameters
    extra_fields = set(request_data.keys()) - set(required_fields.keys())
    if extra_fields:
        raise ValueError("Extra parameter detected")

    # Validate required fields
    for field, field_type in required_fields.items():
        if field not in request_data:
            raise ValueError(f"Missing '{field}' in request data")
        if not isinstance(request_data[field], field_type):
            raise ValueError(f"'{field}' is not of type {field_type.__name__}")