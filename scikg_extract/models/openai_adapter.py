"""
OpenAI model adapter for SciKGExtract.

Implements ModelAdapter using the OpenAI Chat API (via langchain-openai). Supports both plain text and Pydantic-structured outputs, and wraps all calls in retry logic to handle transient API errors.
"""
# Python Imports
import os

# Pydantic Imports
from pydantic import BaseModel

# Langchain Imports
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Scikg_extract Model Imports
from scikg_extract.models.model_adapter import ModelAdapter

class Openai_Adapter(ModelAdapter):
    """
    Openai_Adapter is a subclass of ModelAdapter which has a task of doing inference from the specific OpenAI model
    giving a specified prompt.
    """

    def __init__(self, model_name: str, temperature: float = 0.3, response_format: str = None) -> None:
        """
        Initializes the OpenAI adapter with the specified model configuration. (API Key, Organization ID, Model name etc.)
        Args:
            model_name (str): The name of the OpenAI model to use.
            temperature (float, optional): Sampling temperature for response generation. Defaults to 0.3.
            response_format (str, optional): Desired response format type. If not provided, uses the default from configuration.
        Raises:
            AssertionError: If the OpenAI API key or Organization ID is not set in the configuration.
        """
        super().__init__(model_name=model_name, temperature=temperature)

        # API Key of OpenAI
        assert self.config.OPENAI_api_key is not None
        self.api_key = self.config.OPENAI_api_key
        os.environ["OPENAI_API_KEY"] = self.api_key

        # Organization ID of OpenAI 
        # (Optional, can be provided if the user has multiple organizations in OpenAI and wants to specify which one to use)
        if self.config.OPENAI_organization_id is not None:
            self.organization_id = self.config.OPENAI_organization_id
            os.environ["OPENAI_ORGANIZATION"] = self.organization_id

        # Response Format
        self.response_format = response_format or self.config.OPENAI_response_format

        # Number of retry if model returns any error
        self.num_entry = self.config.OPENAI_num_retry

        # Max output tokens for the model
        self.max_tokens = self.config.OPENAI_max_tokens

        # The Large Language Model to use for Inference
        self.model = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            timeout=self.config.OPENAI_request_timeout,
            max_tokens=self.max_tokens,
            model_kwargs={"response_format": {"type": self.response_format}} if self.response_format else None,
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of an object
        """
        return f"OPENAI - LLM Inference with Model: {self.model_name}"

    def completion(self, prompt_template, var_dict: dict) -> str | None:
        """
        Calls the completion API of the OpenAI model using a formatted prompt and returns the parsed output.
        Args:
            prompt_template (str): The prompt template containing placeholders for dynamic values.
            var_dict (dict): A dictionary mapping variable names to their corresponding values for prompt formatting.
        Returns:
            str | None: The parsed output from the language model, or None if an exception occurs.
        """
        try:
            # Formatting the prompt
            prompt = ModelAdapter.format_prompt_template(prompt_template, var_dict)

            def _invoke():
                # Invoking the model's completion API with the prompt
                model_output = self.model.invoke(prompt.to_messages())

                # Parsing and returning the model's output as string
                return StrOutputParser().invoke(model_output)
            
            # Calling the _invoke function with retry mechanism
            return self._invoke_with_retry(_invoke, self.num_entry)
        except Exception as e:
            self.logger.debug(
                f"Exception Occurred while calling the Completion API of model: {self.model_name}"
            )
            self.logger.debug(f"Exception: {e}")
            return None
        
    def structured_completion(self, prompt_template, var_dict: dict, data_model: BaseModel) -> BaseModel | None:
        """
        Calls the structured completion API of the OpenAI model using a formatted prompt and returns the parsed structured output.
        Args:
            prompt_template (str): The prompt template containing placeholders for dynamic values.
            var_dict (dict): A dictionary mapping variable names to their corresponding values for prompt formatting.
            data_model (BaseModel): The Pydantic BaseModel class that defines the structure of the expected output.
        Returns:
            BaseModel | None: The parsed structured output from the language model as an instance of the provided data model, or None if an exception occurs.
        """
        try:
            # Formatting the prompt
            prompt = ModelAdapter.format_prompt_template(prompt_template, var_dict)

            # Wrap the model with structured output (include_raw=True to access raw response on parse failure)
            structured_model = self.model.with_structured_output(data_model, include_raw=True)

            def _invoke():
                # Invoking the model's structured completion API with the prompt and returning the structured output 
                # as an instance of the provided data model
                result = structured_model.invoke(prompt.to_messages())

                # If parsing succeeded, return the parsed model directly
                if result["parsed"] is not None:
                    return result["parsed"]

                # Parsing failed — attempt list-wrapping fallback
                raw_content = result["raw"].content if result.get("raw") else ""
                return ModelAdapter._try_wrap_list_output(raw_content, data_model, result["parsing_error"])
            
            # Calling the _invoke function with retry mechanism
            return self._invoke_with_retry(_invoke, self.num_entry)
        except Exception as e:
            self.logger.debug(
                f"Exception Occurred while calling the Structured Completion API of model: {self.model_name}"
            )
            self.logger.debug(f"Exception: {e}")
            return None
