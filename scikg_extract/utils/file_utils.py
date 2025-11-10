import json
import logging
import os
from pathlib import Path

import yaml

def read_yaml_file(file_path: str, enc: str = "utf-8"):
    """
    Reads a YAML Configuration file and returns the content in a dictionary format
    Args:
        file_path (str): The path to the YAML file
        enc (str, optional): The encoder to use for reading the file. Defaults to "utf-8".
    Returns:
        dict: The content of the YAML file in a dictionary format. In case of exception, 'None' is returned!
    """
    # Initialize the logger
    logger = logging.getLogger(__name__)
    try:
        with open(file=file_path, mode="r", encoding=enc) as f:
            cfg = yaml.safe_load(f)
        return cfg
    except FileNotFoundError:
        logger.debug(f"File NOT Found at path: {file_path}")
    except Exception as e:
        logger.debug(f"Exception occured: {e},\nType: {type(e)}")
    return None

def read_json_file(filepath: str, encoding: str = "utf-8") -> dict | None:
    """
    Reads a JSON file and returns the content in a dictionary format
    Args:
        filepath (str): The path to the JSON file
        encoding (str, optional): The encoder to use for reading the file. Defaults to "utf-8".
    Returns:
        dict: The content of the JSON file in a dictionary format. In case of exception, 'None' is returned!
    """
    # Initialize the logger
    logger = logging.getLogger(__name__)
    try:
        with open(filepath, "r", encoding=encoding) as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        logger.debug("Cannot parse JSON file: {}".format(filepath))
    except FileNotFoundError:
        logger.debug("File Not Found: {}".format(filepath))
    except Exception as e:
        logger.debug("Exception occured: {}".format(e))
    return None

def save_json_file(filepath, filename, data, encoding="utf-8") -> bool:
    """
    Saves the JSON data to a file at the specified path
    Args:
        filepath (str): The directory path where the file will be saved
        filename (str): The name of the file to save the JSON data
        data (dict): The JSON data to be saved
        encoding (str, optional): The encoder to use for writing the file. Defaults to "utf-8".
    Returns:
        bool: True if the file was saved successfully, otherwise False
    """
    # Initialize the logger
    logger = logging.getLogger(__name__)
    try:
        # Checking if the directory exist, if not create the directory
        os.makedirs(filepath, exist_ok=True)
        filename = "{}/{}".format(filepath, filename)

        # Writing the JSON data on the file
        with open(filename, "w", encoding=encoding) as f:
            json.dump(data, f, indent=4)
        return True
    except json.JSONDecodeError:
        logger.debug("Cannot parse JSON file: {}".format(filepath))
    except Exception as e:
        logger.debug("Exception occured: {}".format(e))
    return False

def read_text_file(file_path: str, enc: str = "utf-8"):
    """
    Reads a text file and returns the content as a string
    Args:
        file_path (str): The path to the text file
        enc (str, optional): The encoder to use for reading the file. Defaults to "utf-8".
    Returns:
        str: The content of the text file as a string. In case of exception, 'None' is returned!
    """
    # Initialize the logger
    logger = logging.getLogger(__name__)
    try:
        with open(file=file_path, mode="r", encoding=enc) as f:
            data = f.read()
        return data
    except FileNotFoundError:
        logger.debug(f"File NOT Found at path: {file_path}")
    except Exception as e:
        logger.debug(f"Exception occured: {e},\nType: {type(e)}")
    return None

def write_text_file(file_path: str, text: str, encoding: str = "utf-8"):
    """
    Writes the given text to a file at the specified path
    Args:
        file_path (str): The path to the file where the text will be written
        text (str): The text content to be written to the file
        encoding (str, optional): The encoder to use for writing the file. Defaults to "utf-8".
    Returns:
        bool: True if the file was written successfully, otherwise False
    """
    # Initialize the logger
    logger = logging.getLogger(__name__)
    try:
        # Checking if the directory exist, if not create the directory
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(text)
        return True
    except Exception as e:
        logger.debug("Exception occured: {}".format(e))
        return False

def load_text_input(input_val: str | Path) -> str:
    """
    Resolve a text input that may be provided as either a file path or a string. If the input corresponds to an existing file path, the file will be read and its contents returned as a string. If the input does not match a valid file path, it is treated as the string itself and returned unchanged.
    Args:
        input_val (str | Path): Either a string or `pathlib.Path` object pointing to a text file.
    Returns:
        str: The resolved text content, either loaded from the file or returned as provided.
    """
    if not isinstance(input_val, (str, Path)):
        raise TypeError("The input must be a string or Path object")
    path = Path(input_val)
    text = read_text_file(str(path)) if path.is_file() else str(input_val)
    return text

def load_json_input(input_val: dict | Path) -> dict | None:
    """
    Resolve a JSON input that may be provided as either a file path or a dictionary. If the input is a `pathlib.Path` object pointing to an existing file, the file will be read and its contents returned as a dictionary. If the input is already a dictionary, it is returned unchanged.
    Args:
        input_val (dict | Path): Either a dictionary or `pathlib.Path` object pointing to a JSON file.
    Returns:
        dict | None: The resolved JSON content. Returns 'None' if loading from file fails.
    """
    if not isinstance(input_val, (dict, Path)):
        raise TypeError("The input must be a dictionary or Path object")
    if isinstance(input_val, Path):
        if input_val.is_file():
            return read_json_file(str(input_val))
        else:
            raise FileNotFoundError(f"JSON file not found: {input_val}")
    return input_val