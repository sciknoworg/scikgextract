import os

from pydantic import BaseModel

from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

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
        assert self.config.OPENAI_organization_id is not None
        self.organization_id = self.config.OPENAI_organization_id
        os.environ["OPENAI_ORGANIZATION"] = self.organization_id

        # Response Format
        self.response_format = response_format or self.config.OPENAI_response_format

        # The Large Language Model to use for Inference
        self.model = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
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

            # Invoking the model's completion API with the prompt
            model_output = self.model.invoke(prompt.to_messages())

            # Parsing the LLM's output to extract the final output
            model_output = StrOutputParser().invoke(model_output)

            # Returns the LLM's output
            return model_output
        except Exception as e:
            self.logger.debug(
                f"Exception Occurred while calling the Completion API of model: {self.model_name}"
            )
            self.logger.debug(f"Exception: {e}")
            return None
        
    def structured_completion(self, prompt_template, var_dict: dict, data_model: BaseModel) -> BaseModel | None:
        try:
            # Formatting the prompt
            prompt = ModelAdapter.format_prompt_template(prompt_template, var_dict)

            # Wrap the model with structured output
            structured_model = self.model.with_structured_output(data_model)

            # Invoking the model's structured completion API with the prompt
            model_output = structured_model.invoke(prompt.to_messages())

            # Returns the LLM's structured output
            return model_output
        except Exception as e:
            self.logger.debug(
                f"Exception Occurred while calling the Structured Completion API of model: {self.model_name}"
            )
            self.logger.debug(f"Exception: {e}")
            return None
