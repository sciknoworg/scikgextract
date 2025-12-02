import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompt_values import PromptValue

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
        

    @abstractmethod
    def completion(self, prompt_template, var_dict) -> Any | None:
        pass

    @abstractmethod
    def structured_completion(self, prompt_template, var_dict, data_model) -> Any | None:
        pass
