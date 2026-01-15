from typing import Optional, List, Any, Dict, Set
from pydantic import BaseModel


def parse_opt_fields(opt_fields: Optional[str]) -> Set[str]:
    """
    Parse the opt_fields query parameter.
    
    Args:
        opt_fields: Comma-separated list of fields to include
    
    Returns:
        Set of field names to include
    """
    if not opt_fields:
        return set()
    
    fields = set()
    for field in opt_fields.split(","):
        field = field.strip()
        if field:
            fields.add(field)
    
    return fields


def filter_fields(data: Dict[str, Any], opt_fields: Set[str]) -> Dict[str, Any]:
    """
    Filter a dictionary to only include specified fields.
    Always includes 'gid' and 'resource_type' if present.
    
    Args:
        data: Dictionary to filter
        opt_fields: Set of field names to include
    
    Returns:
        Filtered dictionary
    """
    if not opt_fields:
        return data
    
    # Always include these fields
    always_include = {"gid", "resource_type"}
    fields_to_include = opt_fields | always_include
    
    result = {}
    for key, value in data.items():
        if key in fields_to_include:
            # Handle nested fields (e.g., "assignee.name")
            if isinstance(value, dict):
                nested_fields = {
                    f.split(".", 1)[1]
                    for f in opt_fields
                    if f.startswith(f"{key}.")
                }
                if nested_fields:
                    result[key] = filter_fields(value, nested_fields)
                else:
                    result[key] = value
            else:
                result[key] = value
    
    return result


def filter_list(data: List[Dict[str, Any]], opt_fields: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter a list of dictionaries to only include specified fields.
    
    Args:
        data: List of dictionaries to filter
        opt_fields: Set of field names to include
    
    Returns:
        List of filtered dictionaries
    """
    if not opt_fields:
        return data
    
    return [filter_fields(item, opt_fields) for item in data]


class OptFieldsParser:
    """Helper class to parse and apply opt_fields filtering."""
    
    def __init__(self, opt_fields: Optional[str] = None):
        self.fields = parse_opt_fields(opt_fields)
    
    def filter(self, data: Any) -> Any:
        """Filter data based on opt_fields."""
        if isinstance(data, list):
            return filter_list(data, self.fields)
        elif isinstance(data, dict):
            return filter_fields(data, self.fields)
        return data
    
    def has_field(self, field: str) -> bool:
        """Check if a specific field is requested."""
        if not self.fields:
            return True  # No filtering means include all
        return field in self.fields or any(f.startswith(f"{field}.") for f in self.fields)


