import re
import string
import unicodedata
from typing import List, Optional, Tuple

def remove_whitespace(s: str) -> str:
    """
    Remove all whitespace characters from the input string.
    Args:
        s (str): The input string.
    Returns:
        str: The string with all whitespace characters removed.
    """
    return ''.join(s.split())

def remove_punctuation(s: str) -> str:
    """
    Remove all punctuation characters from the input string.
    Args:
        s (str): The input string.
    Returns:
        str: The string with all punctuation characters removed.
    """
    return s.translate(str.maketrans('', '', string.punctuation))

def remove_special_characters(s: str) -> str:
    """
    Remove special characters from the input string, keeping only alphanumeric characters and spaces.
    Args:
        s (str): The input string.
    Returns:
        str: The string with special characters removed.
    """
    allowed_chars = string.ascii_letters + string.digits + ' '
    return ''.join(c for c in s if c in allowed_chars)

def normalize_unicode(s: str, form: str = 'NFKD') -> str:
    """
    Normalize unicode characters in the input string to their closest ASCII representation.
    Args:
        s (str): The input string.
        form (str): The normalization form (e.g., 'NFKD', 'NFC', etc.).
    Returns:
        str: The normalized string.
    """
    return unicodedata.normalize(form, s)

def collapse_whitespace(s: str) -> str:
    """
    Collapse multiple consecutive whitespace characters into a single space.
    Args:
        s (str): The input string.
    Returns:
        str: The string with collapsed whitespace.
    """
    return re.sub(r'\s+', ' ', s).strip()

def normalize_dashes(s: str) -> str:
    """
    Normalize different types of dashes in the input string to a standard hyphen-minus (-).
    Args:
        s (str): The input string.
    Returns:
        str: The string with normalized dashes.
    """
    return re.sub(r'\u2013|\u2014|\u2015', '-', s)  # en-dash, em-dash, horizontal bar

def remove_surrounding_quotes(s: str) -> str:
    """
    Remove surrounding quotes from the input string.
    Args:
        s (str): The input string.
    Returns:
        str: The string with surrounding quotes removed.
    """
    return re.sub(r'^[\'"]|[\'"]$', ' ', s).strip()

def normalize_string(s: str) -> str:
    """
    Perform a series of normalization steps on the input string.
    Args:
        s (str): The input string.
    Returns:
        str: The normalized string.
    """

    # Apply normalization steps
    s = s.lower()
    s = remove_whitespace(s)
    s = remove_punctuation(s)
    s = remove_special_characters(s)
    s = normalize_unicode(s)
    s = collapse_whitespace(s)
    s = normalize_dashes(s)
    s = remove_surrounding_quotes(s)
    
    # Return the normalized string
    return s

def filter_containing(list_str: List[str], substr: str) -> List[str]:
    """
    Filter a list of strings to include only those that contain a specific substring.
    Args:
        list_str (List[str]): The list of strings to filter.
        substr (str): The substring to check for.
    Returns:
        List[str]: A list of strings that contain the specified substring.
    """
    return [s for s in list_str if substr.lower() in s.lower()]

def parse_path(path: str) -> List[Tuple[str, Optional[int]]]:
    """
    Parse a dot-notation path into a list of (key, index) tuples.
    Args:
        path: Dot-notation path string
    Returns:
        List of tuples where each tuple is (key, index). Index is None if not specified,
        -1 for wildcard '*', or an integer for specific indices.
    """

    # Initialize the list to hold parsed parts
    parts = []
    
    # Split by dots
    segments = path.split('.')
    
    # Iterate through each segment
    for segment in segments:
        
        # Check if segment has array notation: key[index] or key[*]
        match = re.match(r'^([^\[]+)\[([^\]]+)\]$', segment)
        
        # If it matches the array notation
        if match:
            key = match.group(1)
            index_str = match.group(2)

            # Wildcard - process all items
            if index_str == '*':
                parts.append((key, -1))
            else:
                # Specific index
                try:
                    index = int(index_str)
                    parts.append((key, index))
                except ValueError:
                    # Invalid index, treat as regular key
                    parts.append((segment, None))
        else:
            # Regular key without array notation
            parts.append((segment, None))
    
    # Return the list of parsed parts
    return parts