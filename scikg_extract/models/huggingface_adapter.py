"""
HuggingFace model adapter for SciKGExtract.

Implements ModelAdapter using locally loaded HuggingFace Transformers models. Supports GPU acceleration via PyTorch and is intended for research environments where direct model access or fine-tuned checkpoints are needed. Supports both plain text and Pydantic-structured outputs via constrained decoding.
"""
# Python Imports
import os

# Pydantic Imports
from pydantic import BaseModel

# Pytorch Imports
import torch

# Transformers Imports
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Langchain Imports
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFacePipeline

# Scikg_extract Model Imports
from scikg_extract.models.model_adapter import ModelAdapter

class HuggingFace_Adapter(ModelAdapter):
    """
    HuggingFace_Adapter is a subclass of ModelAdapter which has a task of doing inference from the specific HuggingFace model giving a specified prompt.
    """
    def __init__(self, model_name: str, temperature: float = 0.3, response_format: str | None = None):
        """
        Initializes the HuggingFace adapter with the specified model configuration. (Model name, Temperature, Response format etc.)
        Args:
            model_name (str): The name of the HuggingFace model to use.
            temperature (float, optional): Sampling temperature for response generation. Defaults to 0.3.
            response_format (str, optional): Desired response format type. If not provided, uses the default from configuration.
        """
        super().__init__(model_name, temperature)

        # HuggingFace Access Token
        assert self.config.HUGGINGFACE_access_token is not None
        self.access_token = self.config.HUGGINGFACE_access_token
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = self.access_token
        os.environ["HF_TOKEN"] = self.access_token

        # Context Window Size
        self.context_window_size = self.config.HUGGINGFACE_Context_Window_Size

        # Number of retries for HuggingFace Endpoint calls
        self.num_retry = self.config.HUGGINGFACE_num_retry

        # Request timeout for HuggingFace Endpoint calls
        self.request_timeout = self.config.HUGGINGFACE_request_timeout

        # Set Transformers logging level to error to suppress warnings
        transformers.logging.set_verbosity_error()
        
        if self.config.HUGGINGFACE_use_local:
            self.logger.info(f"Using local HuggingFace model: {self.model_name} for LLM inference")
            tokenizer = AutoTokenizer.from_pretrained(self.model_name, token = self.access_token)
            model = AutoModelForCausalLM.from_pretrained(self.model_name, token = self.access_token, dtype=torch.bfloat16, device_map="auto")
            
            # Create the text generation pipeline using the loaded model and tokenizer
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                trust_remote_code=True,
                max_new_tokens=self.context_window_size,
                temperature=self.temperature,
                max_length=None,
                do_sample=self.temperature > 0
            )

            # Initialize the HuggingFacePipeline with the created pipeline
            self.model = HuggingFacePipeline(
                pipeline=pipe,
                pipeline_kwargs={
                    "max_new_tokens": self.context_window_size,
                    "max_length": None,
                    "temperature": self.temperature,
                    "do_sample": self.temperature > 0,
                }
            )
        else:
            self.logger.info(f"Using HuggingFace inference API with model: {self.model_name} for LLM inference")

            # The Large Language Model to use for Inference
            self.model = HuggingFaceEndpoint(
                repo_id=self.model_name,
                task="text-generation",
                max_new_tokens=self.context_window_size,
                temperature=self.temperature,
                timeout=self.request_timeout,
            )

        # Initialize the Chat Model with the specified HuggingFace model
        self.chat_model = ChatHuggingFace(llm = self.model)

    def __str__(self) -> str:
        """
        Returns a human-readable representation of an object
        """
        return f"HuggingFace - LLM Inference with Model: {self.model_name}"
    
    def completion(self, prompt_template, var_dict) -> str | None:
        """
        Requests the completion endpoint of the HuggingFace model with the specified prompt. Returns the parsed output from the model.
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
                model_output = self.chat_model.invoke(prompt.to_messages())

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
        Requests the completion endpoint of the HuggingFace model with the specified prompt and returns the structured output parsed into the provided data model.
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
            structured_model = self.chat_model.with_structured_output(data_model, include_raw=True)

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