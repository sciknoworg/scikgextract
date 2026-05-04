"""
Ollama model adapter for SciKGExtract.

Implements ModelAdapter using locally hosted models served via Ollama (https://ollama.com). Supports both plain text and Pydantic-structured outputs, and wraps all calls in retry logic to handle transient API errors. Designed for users who want to leverage custom or open-source models in a local environment with low latency.
"""
# Pydantic Imports
from pydantic import BaseModel

# Langchain Imports
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

# Scikg_extract Model Imports
from scikg_extract.models.model_adapter import ModelAdapter

class OLLAMA_Adapter(ModelAdapter):
    """
    OLLAMA_Adapter is a subclass of ModelAdapter which has a task of doing inference from the specific OLLAMA model giving a specified prompt.
    """
    def __init__(self, model_name: str, temperature: float = 0.3, response_format: str | None = None):
        """
        Initializes the OLLAMA adapter with the specified model configuration. (Base URL, Model name etc.)
        Args:
            model_name (str): The name of the OLLAMA model to use.
            temperature (float, optional): Sampling temperature for response generation. Defaults to 0.3.
            response_format (str, optional): Desired response format type. If not provided, uses the default from configuration.
        """
        super().__init__(model_name, temperature)

        # Base URL for OLLAMA Server
        self.base_url = self.config.OLLAMA_base_url or None

        # Context length for the model
        self.context_length = self.config.OLLAMA_context_length

        # Response Format
        self.response_format = self.config.OLLAMA_response_format or response_format

        # Number of retries for API calls
        self.num_retry = 2

        # The Large Language Model to use for Inference
        self.model = ChatOllama(
            base_url=self.base_url,
            model=self.model_name,
            num_ctx=self.context_length,
            temperature=self.temperature,
            format=self.response_format,
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of an object
        """
        return f"OLLAMA - LLM Inference with Model: {self.model_name}"
    
    def completion(self, prompt_template, var_dict) -> str | None:
        """
        Requests the completion endpoint of the OLLAMA service with the specified prompt. Returns the parsed output from the model.
        Args:
            prompt_template: The prompt template containing placeholders for dynamic values.
            var_dict (dict): Dictionary mapping variable names to their values for prompt formatting.
        Returns:
            str | None: The parsed output from the model, or None if no response is obtained after retries.
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
            return self._invoke_with_retry(_invoke, self.num_retry)
        except Exception as e:
            self.logger.debug(f"Exception Occurred while calling the Completion API of model: {self.model_name}")
            self.logger.debug(f"Exception: {e}")
            return None
        
    def structured_completion(self, prompt_template, var_dict: dict, data_model: BaseModel) -> BaseModel | None:
        """
        Requests the completion endpoint of the OLLAMA service with the specified prompt and returns the structured output parsed into the provided data model.
        Args:
            prompt_template: The prompt template containing placeholders for dynamic values.
            var_dict (dict): Dictionary mapping variable names to their values for prompt formatting.
            data_model (BaseModel): The Pydantic BaseModel class that defines the structure of the expected output.
        Returns:
            BaseModel | None: The structured output from the model parsed into the provided data model, or None if no response is obtained after retries.
        """
        try:
            # Formatting the prompt
            prompt = ModelAdapter.format_prompt_template(prompt_template, var_dict)

            # Wrap the model with structured output (include_raw=True to access raw response on parse failure)
            structured_model = self.model.with_structured_output(data_model, include_raw=True)

            def _invoke():
                # Invoking the model's completion API with the prompt and returning the structured output 
                # as an instance of the provided data model
                result = structured_model.invoke(prompt.to_messages())

                # If parsing succeeded, return the parsed model directly
                if result["parsed"] is not None:
                    return result["parsed"]

                # Parsing failed — attempt list-wrapping fallback
                raw_content = result["raw"].content if result.get("raw") else ""
                return ModelAdapter._try_wrap_list_output(raw_content, data_model, result["parsing_error"])
            
            # Calling the _invoke function with retry mechanism
            return self._invoke_with_retry(_invoke, self.num_retry)
        except Exception as e:
            self.logger.debug(f"Exception Occurred while calling the Structured completion API of model: {self.model_name}")
            self.logger.debug(f"Exception: {e}")
            return None