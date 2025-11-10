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

        # The Large Language Model to use for Inference
        self.model = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature,
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
        """

        # Initializing model output
        model_output = None

        # Resetting number of retry count
        self.num_retry = self.config.SAIA_num_retry

        # Iterating until we get a response from the model or the number of retry is exhausted
        while not model_output:
            try:
                # Formatting the prompt
                prompt = ModelAdapter.format_prompt_template(prompt_template, var_dict)

                # Invoking the model's completion API with the prompt
                model_output = self.model.invoke(prompt.to_messages())

                # Parsing the LLM's output to extract the final output
                model_output = StrOutputParser().invoke(model_output)
            except Exception as e:
                self.logger.debug(f"Exception Occurred while calling the Completion API of model: {self.model_name}")
                self.logger.debug(f"Exception: {e}")

                # Checking if number of retry's are left, otherwise returning from the method
                if self.num_retry > 0:
                    self.num_retry -= 1
                    self.logger.debug(f"Retrying again with the same prompt, current retry count: {self.num_retry}")
                else:
                    self.logger.debug("Number of retry is finished, returning from the model")
                    break

        # Returns the LLM's output
        return model_output
    
    def structured_completion(self, prompt_template, var_dict: dict, data_model: BaseModel) -> BaseModel | None:
        # Initializing model output
        model_output = None

        # Resetting number of retry count
        self.num_retry = self.config.SAIA_num_retry

        # Iterating until we get a response from the model or the number of retry is exhausted
        while not model_output:
            try:
                # Formatting the prompt
                prompt = ModelAdapter.format_prompt_template(prompt_template, var_dict)

                # Wrap the model with structured output
                structured_model = self.model.with_structured_output(data_model)

                # Invoking the model's completion API with the prompt
                model_output = structured_model.invoke(prompt.to_messages())
            except Exception as e:
                self.logger.debug(f"Exception Occurred while calling the Completion API of model: {self.model_name}")
                self.logger.debug(f"Exception: {e}")

                # Checking if number of retry's are left, otherwise returning from the method
                if self.num_retry > 0:
                    self.num_retry -= 1
                    self.logger.debug(f"Retrying again with the same prompt, current retry count: {self.num_retry}")
                else:
                    self.logger.debug("Number of retry is finished, returning from the model")
                    break

        # Returns the LLM's output
        return model_output
