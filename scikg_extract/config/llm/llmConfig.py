# Python imports
import asyncio
from dataclasses import dataclass

# Scikg_Extract Config Imports
from scikg_extract.config.llm.envConfig import EnvConfig

# Scikg_Extract LLM Model Adapter Imports
from scikg_extract.models.model_adapter import ModelAdapter
from scikg_extract.models.openai_adapter import Openai_Adapter
from scikg_extract.models.saia_adapter import SAIA_Adapter

# Scikg_Extract Evaluation Judge Imports
from scikg_extract.evaluation.judges.openai_judge import OpenAIJudge
from scikg_extract.evaluation.judges.saia_judge import SaiaJudge

# Scikg_Extract Utility Imports
from scikg_extract.utils.rest_client import RestClient

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

# Registry of available LLM configurations
LLM_REGISTRY = {
    "gpt-4o": LLMConfig(
        model_name="gpt-4o",
        inference_adapter=Openai_Adapter,
        evaluation_judge=OpenAIJudge
    ),
    "gpt-5-mini": LLMConfig(
        model_name="gpt-5-mini",
        inference_adapter=Openai_Adapter,
        evaluation_judge=OpenAIJudge
    ),
    "gpt-5": LLMConfig(
        model_name="gpt-5",
        inference_adapter=Openai_Adapter,
        evaluation_judge=OpenAIJudge
    )
}

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

    # Return the list of SAIA model names
    return saia_models

# Fetch SAIA LLM models asynchronously
saia_models = asyncio.run(get_saia_models())

# Add SAIA models dynamically to the LLM registry
for model_name in saia_models:
    LLM_REGISTRY[model_name] = LLMConfig(
        model_name=model_name,
        inference_adapter=SAIA_Adapter,
        evaluation_judge=SaiaJudge
    )