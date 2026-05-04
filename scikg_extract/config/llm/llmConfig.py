"""
LLMConfig Module for SciKGExtract. 

This module defines the configuration classes and registry for managing different Large Language Models (LLMs) and their corresponding adapters and judges within the SciKG-Extract framework. It includes functionality to discover available models from registered providers and resolve the appropriate configuration based on model and provider names.
"""
# Python imports
import asyncio
import inspect
from dataclasses import dataclass
from typing import Callable

# Scikg_Extract Config Imports
from scikg_extract.config.llm.envConfig import EnvConfig

# Scikg_Extract LLM Model Adapter Imports
from scikg_extract.models.model_adapter import ModelAdapter
from scikg_extract.models.openai_adapter import Openai_Adapter
from scikg_extract.models.saia_adapter import SAIA_Adapter
from scikg_extract.models.ollama_adapter import OLLAMA_Adapter
from scikg_extract.models.huggingface_adapter import HuggingFace_Adapter

# Scikg_Extract Evaluation Judge Imports
from scikg_extract.evaluation.judges.openai_judge import OpenAIJudge
from scikg_extract.evaluation.judges.saia_judge import SaiaJudge
from scikg_extract.evaluation.judges.ollama_judge import OllamaJudge
from scikg_extract.evaluation.judges.huggingface_judge import HuggingFaceJudge

# Scikg_Extract Utility Imports
from scikg_extract.utils.rest_client import RestClient
from scikg_extract.utils.log_handler import LogHandler

# Yescieval Judge Import
from yescieval.base.judge import Judge

@dataclass
class LLMConfig:
    """
    Configuration dataclass for managing different Large Language Models (LLMs) in SciKG-Extract framework.
    """
    # LLM model name
    model_name: str

    # Inference adapter class for the LLM
    inference_adapter: type[ModelAdapter]

    # Evaluation judge class for the LLM
    evaluation_judge: type[Judge]

@dataclass
class ProviderConfig:
    """
    Configuration dataclass for managing LLM providers in SciKG-Extract framework.
    """
    # LLM provider name
    provider_name: str

    # Inference adapter class for the provider
    inference_adapter: type[ModelAdapter]

    # Evaluation judge class for the provider
    evaluation_judge: type[Judge]

    # Optional callable to discover available models for the provider
    discover_models: Callable | None

    # Set of known model names for the provider
    known_models: set[str]

class ProviderRegistry:
    """
    Registry class to manage LLM providers and their configurations in SciKG-Extract framework. This class allows for registering new providers, discovering available models, and resolving the appropriate LLM configuration based on model and provider names.
    """

    # Registry of available LLM providers and their configurations
    providers: dict[str, ProviderConfig] = {}

    @classmethod
    def register(cls, provider_name: str, provider_config: ProviderConfig) -> None:
        """
        Registers a new LLM provider configuration in the registry.
        Args:
            provider_name (str): The name of the LLM provider (e.g., "OPENAI", "SAIA", "OLLAMA").
            provider_config (ProviderConfig): The configuration object containing adapter, judge, and discovery info.
        """
        cls.providers[provider_name] = provider_config

    @classmethod
    def discover_all(cls) -> None:
        """
        Discovers available models for all registered LLM providers that have a discovery function defined. This method iterates through each provider in the registry and calls its discover_models function to populate the known_models set with available model names.
        """
        # Initialize the logger
        logger = LogHandler.get_logger(__name__)
        logger.debug("Discovering available models for all registered LLM providers...")

        # Iterate through all registered providers and discover their models if a discovery function is provided
        for provider_name, config in cls.providers.items():
            if config.discover_models:
                try:
                    if inspect.iscoroutinefunction(config.discover_models):
                        models = asyncio.run(config.discover_models())
                    else:
                        models = config.discover_models()
                    config.known_models.update(models)
                    logger.debug(f"Discovered models for {provider_name}: {models}")
                except Exception as e:
                    logger.debug(f"Error discovering models for {provider_name}: {e}")

    @classmethod
    def resolve(cls, model_name: str, provider_name: str = None) -> LLMConfig:
        """
        Resolves the appropriate LLM configuration based on the provided model name and optional provider name. This method checks if the specified model name exists in the known_models set of the specified provider or across all providers if no provider is specified, and returns the corresponding LLMConfig with the correct adapter and judge.
        Args:
            model_name (str): The name of the model to resolve (e.g., "gpt-4o", "gpt-5-mini").
            provider_name (str, optional): The name of the provider to filter by (e.g., "OPENAI"). If None, checks across all providers.
        Returns:
            LLMConfig: The configuration object containing the adapter and judge for the resolved model.
        Raises:
            ValueError: If the model name is not found in the registry for the specified provider or across all providers.
        """
        if provider_name:
            provider = cls.providers.get(provider_name)
            if not provider:
                raise ValueError(f"Provider '{provider_name}' not found in the registry.")
            return LLMConfig(
                model_name=model_name,
                inference_adapter=provider.inference_adapter,
                evaluation_judge=provider.evaluation_judge
            )
        else:
            for provider in cls.providers.values():
                if model_name in provider.known_models:
                    return LLMConfig(
                        model_name=model_name,
                        inference_adapter=provider.inference_adapter,
                        evaluation_judge=provider.evaluation_judge
                    )
        raise ValueError(f"Model '{model_name}' not found in any providers")
    
    @classmethod
    def has_model_or_provider(cls, model_name: str, provider_name: str = None) -> bool:
        """
        Check if a model name or provider name exists in the registry. This method checks if the specified model name exists in the known_models set of the specified provider or across all providers if no provider is specified.
        Args:
            model_name (str): The name of the model to check (e.g., "gpt-4o", "gpt-5-mini").
            provider_name (str, optional): The name of the provider to filter by (e.g., "OPENAI"). If None, checks across all providers.
        """
        if provider_name:
            provider = cls.providers.get(provider_name)
            if provider:
                return True
        else:
            for provider in cls.providers.values():
                if model_name in provider.known_models:
                    return True
        return False   

    @classmethod
    def parse_llm_string(cls, llm_string: str) -> tuple[str, str | None]:
        """
        Parses a combined 'PROVIDER:model_name' string into its components. Only treats the part before the first colon as a provider if it matches a registered provider name; otherwise the entire string is treated as a model name.
        Args:
            llm_string (str): The combined string (e.g., "OPENAI:gpt-4o") or just a model name (e.g., "gpt-4o", "llama3:70b").
        Returns:
            tuple[str, str | None]: A tuple of (model_name, provider_name). provider_name is None if no provider prefix is found.
        """
        if ":" in llm_string:
            prefix, rest = llm_string.split(":", 1)
            if prefix.strip().upper() in cls.providers:
                return rest.strip(), prefix.strip().upper()
        return llm_string.strip(), None

    @classmethod
    def resolve_from_string(cls, llm_string: str) -> LLMConfig:
        """
        Resolves the LLM configuration from a combined 'PROVIDER:model_name' string.
        Args:
            llm_string (str): The combined string (e.g., "OPENAI:gpt-4o") or just a model name.
        Returns:
            LLMConfig: The resolved configuration.
        """
        model_name, provider_name = cls.parse_llm_string(llm_string)
        return cls.resolve(model_name, provider_name)

    @classmethod
    def has_model_or_provider_from_string(cls, llm_string: str) -> bool:
        """
        Checks if a combined 'PROVIDER:model_name' string can be resolved in the registry.
        Args:
            llm_string (str): The combined string (e.g., "OPENAI:gpt-4o") or just a model name.
        Returns:
            bool: True if the model/provider exists in the registry.
        """
        model_name, provider_name = cls.parse_llm_string(llm_string)
        return cls.has_model_or_provider(model_name, provider_name)

async def get_saia_models() -> list[str]:
    """
    Retrieves the list of SAIA model names from the LLM registry.
    Returns:
        list[str]: A list of model names that use the SAIA adapter.
    """
    
    # Initialize the RestClient
    client = RestClient(base_url=EnvConfig.SAIA_base_url, api_key=EnvConfig.SAIA_api_key)

    # Fetch the list of available models from SAIA
    response = await client.get("/models")

    # Extract model names from the response
    saia_models = [model["id"] for model in response.get("data", [])]
    print(f"Discovered SAIA models: {saia_models}")

    # Return the list of SAIA model names
    return saia_models

async def get_ollama_models() -> list[str]:
    """
    Retrieves the list of OLLAMA model names for the LLM registry.
    Returns:
        list[str]: A list of model names that use the OLLAMA adapter.
    """

    # Initialize the RestClient
    client = RestClient(base_url=EnvConfig.OLLAMA_base_url)

    # Fetch the list of available models from OLLAMA
    response = await client.get("api/tags")

    # Extract model names from the response
    ollama_models = [model["name"] for model in response.get("models", [])]

    # Return the list of OLLAMA model names
    return ollama_models

# Registering providers in the ProviderRegistry
ProviderRegistry.register(
    provider_name="OPENAI",
    provider_config=ProviderConfig(
        provider_name="OPENAI",
        inference_adapter=Openai_Adapter,
        evaluation_judge=OpenAIJudge,
        discover_models=None,
        known_models={"gpt-4o", "gpt-5-mini", "gpt-5"}
    )
)

ProviderRegistry.register(
    provider_name="SAIA",
    provider_config=ProviderConfig(
        provider_name="SAIA",
        inference_adapter=SAIA_Adapter,
        evaluation_judge=SaiaJudge,
        discover_models=get_saia_models,
        known_models=set()
    )
)

ProviderRegistry.register(
    provider_name="OLLAMA",
    provider_config=ProviderConfig(
        provider_name="OLLAMA",
        inference_adapter=OLLAMA_Adapter,
        evaluation_judge=OllamaJudge,
        discover_models=get_ollama_models,
        known_models=set()
    )
)

ProviderRegistry.register(
    provider_name="HUGGINGFACE",
    provider_config=ProviderConfig(
        provider_name="HUGGINGFACE",
        inference_adapter=HuggingFace_Adapter,
        evaluation_judge=HuggingFaceJudge,
        discover_models=None,
        known_models=set()
    )
)

# Discover available models for all registered providers
ProviderRegistry.discover_all()