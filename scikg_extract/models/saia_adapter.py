"""
SAIA (Secure AI API) model adapter for SciKGExtract.

Implements ModelAdapter using the SAIA API endpoint, which is OpenAI-compatible but targets internally hosted or third-party models. Wraps all calls in retry logic to handle transient API errors and supports both plain text and Pydantic-structured outputs.
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from pydantic import BaseModel

from scikg_extract.models.model_adapter import ModelAdapter


class SAIA_Adapter(ModelAdapter):
    """
    SAIA_Adapter is a subclass of ModelAdapter which has a task of doing inference from the specific Open source
    Large Language Model(LLM) giving a specified prompt.
    """

    def __init__(self, model_name: str, temperature: float = 0.3, response_format: str = None) -> None:
        """
        Initializes the SAIA adapter with the specified model configuration (Base URL, API Key, Model name etc.)
        Args:
            model_name (str): The name of the language model to use for inference.
            temperature (float, optional): Sampling temperature for model responses. Defaults to 0.3.
            response_format (str, optional): Desired response format type. If not provided, uses the default from configuration.
        """
        super().__init__(model_name=model_name, temperature=temperature)

        # Base URL of the Scalable AI Accelerator (SAIA) platform
        self.base_url = self.config.SAIA_base_url

        # API Key of the SAIA Chat AI
        self.api_key = self.config.SAIA_api_key

        # Number of retry if model returns any error
        self.num_retry = self.config.SAIA_num_retry

        # Response Format
        self.response_format = response_format or self.config.SAIA_response_format

        # Max output tokens for the model
        self.max_tokens = self.config.SAIA_max_tokens

        # The Large Language Model to use for Inference
        self.model = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature,
            timeout=self.config.SAIA_request_timeout,
            max_tokens=self.max_tokens,
            model_kwargs={"response_format": {"type": self.response_format}},
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of an object
        """
        return f"SAIA - LLM Inference with Model: {self.model_name}"

    def completion(self, prompt_template, var_dict: dict) -> str | None:
        """
        Requests the completion endpoint of the SAIA service with the specified prompt/message. Returns the parsed output from the model.
        Args:
            prompt_template: The prompt template containing placeholders for dynamic values.
            var_dict (dict): Dictionary mapping variable names to their values for prompt formatting.
        Returns:
            str | None: The parsed output from the model, or None if no response is obtained after retries.
        Raises:
            RuntimeError: If the maximum number of retries is exhausted without obtaining a response from the model.
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
        Requests the completion endpoint of the SAIA service with the specified prompt/message and returns the structured output parsed into the provided data model.
        Args:
            prompt_template: The prompt template containing placeholders for dynamic values.
            var_dict (dict): Dictionary mapping variable names to their values for prompt formatting.
            data_model (BaseModel): The Pydantic BaseModel class to parse the structured output into.
        Returns:
            BaseModel | None: The structured output from the model parsed into the provided data model, or None if no response is obtained after retries.
        Raises:
            RuntimeError: If the maximum number of retries is exhausted without obtaining a response from the model.
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
            self.logger.debug(f"Exception Occurred while calling the Completion API of model: {self.model_name}")
            self.logger.debug(f"Exception: {e}")
            return None
