from typing import Any, List, Tuple

from scikg_extract.utils.string_utils import parse_path

def is_primitive(val: Any) -> bool:
    """
    Check if a value is a primitive type (str, int, float, bool, None).
    Args:
        val (Any): The value to check.
    Returns:
        bool: True if the value is a primitive type, otherwise False.
    """
    return isinstance(val, (str, int, float, bool)) or val is None

def remove_null_values(data: dict, skip_keys: list = []) -> dict:
    """
    Recursively remove keys with null values from a JSON-like dictionary.
    Args:
        data (dict): The input JSON-like dictionary.
        skip_keys (list): List of keys to skip from removal even if they have null or empty values.
    Returns:
        dict: The cleaned dictionary with null values removed.
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            
            # Skip keys that are in the skip_keys list
            if key in skip_keys:
                cleaned[key] = value
                continue
            
            # Recursively clean the value
            cleaned_value = remove_null_values(value, skip_keys=skip_keys)
            
            # Keep it only if it's not None, not empty dict, not empty list
            if cleaned_value not in ("Not Found", None, {}, []):
                cleaned[key] = cleaned_value
        
        # Return the cleaned dictionary
        return cleaned
    elif isinstance(data, list):

        # Recursively clean each item in the list
        cleaned_list = [remove_null_values(item, skip_keys=skip_keys) for item in data]

        # Filter out empty items (None, {}, [])
        cleaned_list = [item for item in cleaned_list if item not in (None, {}, [])]
        return cleaned_list
    else:
        # Base case: return the value unchanged
        return data

def is_empty_qudt_structure(obj):
    """
    Determines if an object only contains QUDT metadata without actual measurement values.
    
    An object is considered empty if it only has metadata (quantityKind, hasQuantityKind, 
    sameAs, unit) but lacks actual data like numericValue.
    
    Args:
        obj (dict): The object to check
    Returns:
        bool: True if the object should be removed, False otherwise
    """
    if not isinstance(obj, dict) or not obj:
        return False
    
    # QUDT metadata keys that don't represent actual data
    qudt_metadata_keys = {'quantityKind', 'hasQuantityKind', 'sameAs', 'unit'}
    
    keys = set(obj.keys())
    
    # Case 1: Only pure metadata keys (no quantityValue at all)
    if keys.issubset(qudt_metadata_keys):
        return True
    
    # Case 2: Has quantityValue - check if it contains actual data
    if 'quantityValue' in obj:
        quantity_value = obj.get('quantityValue', {})
        
        if not isinstance(quantity_value, dict):
            return False
        
        # If quantityValue has a numeric value, keep the entire structure
        if quantity_value.get('numericValue') is not None:
            return False
        
        # No numeric value - check if rest of object is just metadata
        other_keys = keys - {'quantityValue'}
        if not other_keys or other_keys.issubset(qudt_metadata_keys):
            return True
    
    # Otherwise, keep the object
    return False
    
def remove_empty_qudt_structures(data):
    """
    Recursively removes objects that only contain QUDT metadata without actual values.
    
    An object is considered "empty QUDT structure" if it only contains:
        - quantityKind
        - unit (with hasQuantityKind and/or sameAs)
        - quantityValue (with only unit but no numericValue)
    
    Args:
        data: The data structure to clean (dict, list, or primitive)  
    Returns:
        The cleaned data structure, or None if the entire structure should be removed
    """
    # Handle lists
    if isinstance(data, list):
        cleaned_list = [remove_empty_qudt_structures(item) for item in data]
        cleaned_list = [item for item in cleaned_list if item is not None]
        return cleaned_list if cleaned_list else []
    
    # Handle non-dict primitives (str, int, float, bool, etc.)
    if not isinstance(data, dict):
        return data
    
    # Handle dictionaries
    cleaned_dict = {}
    
    # Special case: preserve quantityValue with numericValue intact (including unit metadata)
    quantity_value = data.get('quantityValue')
    has_numeric_value = (
        isinstance(quantity_value, dict) and 
        quantity_value.get('numericValue') is not None
    )
    
    for key, value in data.items():
        # Preserve quantityValue as-is if it has numericValue
        if key == 'quantityValue' and has_numeric_value:
            cleaned_dict[key] = value
        else:
            # Recursively clean other values
            cleaned_value = remove_empty_qudt_structures(value)
            if cleaned_value is not None:
                cleaned_dict[key] = cleaned_value
    
    # Check if the entire dict is empty QUDT structure
    if is_empty_qudt_structure(cleaned_dict):
        return None
    
    # Remove any nested empty QUDT structures
    final_dict = {}
    for key, value in cleaned_dict.items():
        if not (isinstance(value, dict) and is_empty_qudt_structure(value)):
            final_dict[key] = value
    
    return final_dict if final_dict else None

def get_value_by_path(data: Any, path: str) -> List[Tuple[Any, str]]:
    """
    Extract value(s) from nested data structure using dot-notation path.
    Args:
        data: The data structure to extract from (dict, list, or primitive)
        path: Dot-notation path string   
    Returns:
        List of (value, actual_path) tuples. Empty list if path not found.
        The actual_path shows the concrete path (e.g., "foo[0].bar" instead of "foo[*].bar")
    """
    # Parse the path into components
    parsed_path = parse_path(path)
    
    # Start with the root data
    results = [(data, "")]
    
    for key, index in parsed_path:
        new_results = []
        
        for current_data, current_path in results:
            # Skip if current data is None
            if current_data is None: continue
            
            # Handle dictionary access
            if isinstance(current_data, dict):
                if key not in current_data:
                    continue
                
                value = current_data[key]
                new_path = f"{current_path}.{key}" if current_path else key
                
                # If index is specified, handle array access
                if index is not None:
                    if not isinstance(value, list): continue
                    
                    if index == -1:
                        # Wildcard - add all items
                        for i, item in enumerate(value):
                            new_results.append((item, f"{new_path}[{i}]"))
                    else:
                        # Specific index
                        if 0 <= index < len(value):
                            new_results.append((value[index], f"{new_path}[{index}]"))
                else:
                    # No index - just add the value
                    new_results.append((value, new_path))
            
            # Handle list access (in case path starts with a list)
            elif isinstance(current_data, list):
                if index == -1:
                    # Wildcard on list
                    for i, item in enumerate(current_data):
                        if isinstance(item, dict) and key in item:
                            new_results.append((item[key], f"{current_path}[{i}].{key}"))
                elif index is not None and 0 <= index < len(current_data):
                    # Specific index on list
                    item = current_data[index]
                    if isinstance(item, dict) and key in item:
                        new_results.append((item[key], f"{current_path}[{index}].{key}"))
        
        results = new_results
        
        # If no results found, path doesn't exist
        if not results:
            return []
    
    return results

def set_value_by_path(data: Any, path: str, value: Any) -> bool:
    """
    Set a value in nested data structure using dot-notation path.
    Args:
        data: The data structure to modify (dict or list)
        path: Dot-notation path string (e.g., "foo.bar[0].baz")
        value: The value to set  
    Returns:
        True if value was set successfully, False if path doesn't exist
    """
    # Parse the path into components
    parsed_path = parse_path(path)
    
    # Navigate to the parent of the target
    current = data
    
    # Iterate over the path except the last part
    for key, index in parsed_path[:-1]:

        if not isinstance(current, dict): return False

        # Check if key exists
        if key not in current: return False
        
        # Update the current reference
        current = current[key]
        
        # Handle array access
        if index is not None:
            
            # Go to the specified index
            if not isinstance(current, list) or index >= len(current): return False
            current = current[index]
    
    # Set the final value
    final_key, final_index = parsed_path[-1]

    if isinstance(current, dict):
        # Handle array index if specified
        if final_index is not None:

            # Final key should be an array
            if final_key not in current: return False
            target = current[final_key]
            
            # Update the specified index
            if not isinstance(target, list) or final_index >= len(target): return False
            target[final_index] = value
        else:
            # Simple key assignment
            current[final_key] = value
        
        # Return success
        return True
    
    # Return failure if current is not a dict
    return False

def flatten_record(rec: dict, prefix: str = "") -> List[Tuple[str, Any]]:
    """
    Flatten a dictionary into (property_path, value) pairs.
    Args:
        rec (dict): The record to flatten (could be a dict, list, or primitive).
        prefix (str): The prefix for property paths (used in recursion).
    Returns:
        List[Tuple[str, Any]]: A list of (property_path, value) pairs.
    """
    # Initialize output list
    out: List[Tuple[str, Any]] = []
    
    # Flatten a nested record (dicts/lists) into (property_path, value) pairs.
    if is_primitive(rec):
        out.append((prefix.rstrip(".") or "(root)", rec)) 
        return out

    # Handle dicts
    if isinstance(rec, dict):
        for k, v in rec.items():
            new_prefix = f"{prefix}{k}"
            if is_primitive(v):
                out.append((new_prefix, v))
            else:
                out.extend(flatten_record(v, new_prefix + "."))
        return out

    # Handle lists
    if isinstance(rec, list):
        if not rec:
            return out
        if all(is_primitive(x) for x in rec):
            for v in rec:
                out.append((prefix.rstrip(".") or "(root)", v))
            return out
        for idx, item in enumerate(rec):
            out.extend(flatten_record(item, f"{prefix}[{idx}]."))
        return out
    
    # Return empty if not handled
    return out

def extract_properties_values(records: dict[str, list[dict]], property_path: str) -> list[str]:
    """
    Extract unique property values from JSON data records.
    Args:
        records (dict[str, list[dict]]): JSON data records.
        property_path (str): Dot-separated path to the property.
    Returns:
        list[str]: List of unique property values.
    """
    # Initialize a set to hold unique property values
    property_values = set()

    # Iterate through records and extract property values
    for record in records.values():
        # Iterate through each process entry
        for entry in record["processes"]:
            
            # Extract property values using the specified path
            values = get_value_by_path(entry, property_path)

            # Skip if no values found
            if not values: continue

            # Update the set of unique property values
            for val, _ in values:
                property_values.add(val)
    
    # Return the list of unique property values
    return list(property_values)