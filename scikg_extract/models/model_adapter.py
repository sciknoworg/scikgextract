"""
Abstract base class for LLM model adapters in SciKGExtract.

Defines the common interface (invoke, structured_invoke, _invoke_with_retry) that all concrete adapter implementations (OpenAI, SAIA, Ollama, HuggingFace) must implement. Also provides shared utilities for prompt formatting and Pydantic-schema-based structured output parsing.
"""
# Python Imports
import json
import logging
from typing import Any, get_origin
from abc import ABC, abstractmethod

# Pydantic Imports
from pydantic import BaseModel

# Langchain Imports
from langchain_core.prompt_values import PromptValue
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Scikg_extract Config Imports
from scikg_extract.config.llm.envConfig import EnvConfig

class ModelAdapter(ABC):
    """
    ModelAdapter is an abstract class for doing LLM inference using different Large Language Models (LLMs).
    """

    def __init__(self, model_name: str, temperature: float = 0.3):
        """
        Initializes the object with the specified model name and temperature, reads the configuration file, and sets up logging.
        Args:
            model_name (str): The name of the large language model to use for inference.
            temperature (float, optional): The temperature parameter for the language model, controlling randomness. Defaults to 0.3.
        """

        # The Large Language Model to use for Inference
        self.model_name = model_name

        # LLM Temperature
        self.temperature = temperature

        # Reading the Config File
        self.config = EnvConfig

        # Initialize the logger
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def format_prompt_template(prompt_template, var_dict: dict) -> PromptValue:
        """
        Formats a prompt template by substituting placeholders with values from a variable dictionary.

        Args:
            prompt_template: The prompt template containing the system and user prompt templates with placeholders.
            var_dict (dict): A dictionary mapping variable names to their corresponding values for substitution.
        Returns:
            PromptValue: The formatted prompt with all placeholders replaced by their respective values.
        """
        # Creating the chat prompt template using Langchain
        chat_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_template.system_prompt),
                ("user", prompt_template.user_prompt),
            ]
        )

        # Replacing the placeholders in the prompt with its value
        prompt = chat_prompt_template.invoke(var_dict)

        # Returning the formatted prompt
        return prompt
    
    @staticmethod
    def format_chat_prompt_template(chat_prompt_template, var_dict: dict) -> PromptValue:
        """
        Formats a chat prompt template with MessagesPlaceholder by substituting placeholders with values from a variable dictionary.
        Args:
            chat_prompt_template: The chat prompt template containing system and user prompts along with message placeholders.
            var_dict (dict): A dictionary mapping variable names to their corresponding values for substitution.
        Returns:
            PromptValue: The formatted chat prompt with all placeholders replaced by their respective values. 
        """

        # Creating the chat prompt template with MessagesPlaceholder using Langchain
        chat_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", chat_prompt_template.system_prompt),
                MessagesPlaceholder("chat_history", optional=True),
                ("user", chat_prompt_template.user_prompt),
                MessagesPlaceholder("agent_scratchpad", optional=True)
            ]
        )

        # Replacing the placeholders in the prompt with its value
        prompt = chat_prompt_template.invoke(var_dict)

        # Returning the formatted prompt
        return prompt
        
    @staticmethod
    def _try_wrap_list_output(raw_content: str, data_model: type[BaseModel], original_error: Exception) -> BaseModel:
        """
        Fallback for when the LLM returns a raw JSON array instead of the expected wrapper object.
        Detects if raw_content is a JSON list, finds the single list-typed field in data_model,
        and wraps the array with that field name.
        Args:
            raw_content (str): The raw string content from the LLM response.
            data_model (type[BaseModel]): The Pydantic model class expected by structured output.
            original_error (Exception): The original parsing error to re-raise if wrapping is not applicable.
        Returns:
            BaseModel: The successfully parsed data model instance.
        Raises:
            Exception: Re-raises original_error if the raw content is not a list or wrapping fails.
        """
        logger = logging.getLogger(__name__)

        # Try to parse raw content as JSON
        try:
            raw_json = json.loads(raw_content)
        except (json.JSONDecodeError, TypeError):
            raise original_error

        # Only applies when the LLM returned a list
        if not isinstance(raw_json, list):
            raise original_error

        # Find list-typed fields in the data model
        list_fields = [
            name for name, field_info in data_model.model_fields.items()
            if get_origin(field_info.annotation) is list
        ]

        # Only wrap if there is exactly one list field (unambiguous)
        if len(list_fields) != 1:
            raise original_error

        field_name = list_fields[0]
        logger.warning(
            f"LLM returned a raw JSON array instead of {data_model.__name__}. "
            f"Wrapping with key '{field_name}' as fallback."
        )

        try:
            return data_model(**{field_name: raw_json})
        except Exception:
            raise original_error

    def _invoke_with_retry(self, invoke_func, max_retries: int) -> Any | None:
        """
        Helper method to invoke a function with retry logic. Raises RunTimeError after maximum retries are exhausted.
        Args:
            invoke_func: The function to be invoked with retry logic.
            max_retries (int): The maximum number of retries allowed.
        Returns:
            Any | None: The output from the invoked function, or None if no response is obtained after retries.
        Raises:
            RuntimeError: If the maximum number of retries is exhausted without obtaining a response.
        """
        retries = 0
        while retries < max_retries:
            try:
                return invoke_func()
            except Exception as e:
                self.logger.debug(f"Exception occurred while invoking the model: {self.model_name} with error: {e}")
                retries += 1
                self.logger.debug(f"Retrying... Attempt {retries}/{max_retries}")
        self.logger.debug(f"Maximum retries exhausted. No response obtained from the model: {self.model_name}")
        raise RuntimeError(f"Maximum retries exhausted. No response obtained from the model: {self.model_name}")

    @abstractmethod
    def completion(self, prompt_template, var_dict) -> Any | None:
        pass

    @abstractmethod
    def structured_completion(self, prompt_template, var_dict, data_model) -> Any | None:
        pass
