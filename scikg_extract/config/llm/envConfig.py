"""
Environment variable configuration loader for LLM service credentials.

Loads and exposes API keys, base URLs, and provider-specific settings from environment variables (or a .env file) required by the LLM adapters and judge implementations at runtime.
"""
# Python imports
import os

# External imports
from dotenv import load_dotenv

class EnvConfig:
    """
    Configuration class to load and manage environment variables for LLM services.
    """

    # Loading the environment file
    load_dotenv()

    # OPENAI
    OPENAI_api_key = os.getenv("OPENAI_API_KEY")
    OPENAI_organization_id = os.getenv("OPENAI_ORGANIZATION_ID")
    OPENAI_response_format = "text"
    OPENAI_num_retry = int(os.getenv("OPENAI_NUM_RETRY", 3))
    OPENAI_request_timeout = float(os.getenv("OPENAI_REQUEST_TIMEOUT", 120))
    OPENAI_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", 16384))

    # SAIA
    SAIA_api_key = os.getenv("SAIA_API_KEY")
    SAIA_base_url = os.getenv("SAIA_BASE_URL")
    SAIA_response_format = "text"
    SAIA_num_retry = int(os.getenv("SAIA_NUM_RETRY", 3))
    SAIA_request_timeout = float(os.getenv("SAIA_REQUEST_TIMEOUT", 120))
    SAIA_max_tokens = int(os.getenv("SAIA_MAX_TOKENS", 16384))

    # OLLAMA
    OLLAMA_base_url = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
    OLLAMA_context_length = 32768
    OLLAMA_response_format = "json"

    # HuggingFace
    HUGGINGFACE_access_token = os.getenv("HUGGINGFACE_ACCESS_TOKEN")
    HUGGINGFACE_use_local = os.getenv("HUGGINGFACE_USE_LOCAL", "True").lower() in ("true", "1", "t")
    HUGGINGFACE_Context_Window_Size = int(os.getenv("HUGGINGFACE_CONTEXT_WINDOW_SIZE", 8192))
    HUGGINGFACE_num_retry = int(os.getenv("HUGGINGFACE_NUM_RETRY", 3))
    HUGGINGFACE_request_timeout = float(os.getenv("HUGGINGFACE_REQUEST_TIMEOUT", 120))

    # LLM models with their providers in the format "PROVIDER:MODEL_NAME"
    LLM_EXTRACTION = os.getenv("LLM_EXTRACTION") or None
    LLM_NORMALIZATION = os.getenv("LLM_NORMALIZATION") or None
    LLM_REFLECTION = os.getenv("LLM_REFLECTION") or None
    LLM_SUMMARIZER = os.getenv("LLM_SUMMARIZER") or None
    REFLECTION_JUDGE_MODELS = os.getenv("REFLECTION_JUDGE_MODELS") or None
    REFLECTION_CRITIC_MODELS = os.getenv("REFLECTION_CRITIC_MODELS") or None
    LLM_FEEDBACK = os.getenv("LLM_FEEDBACK") or None

    # SciKGExtract Configuration
    NORMALIZE_EXTRACTED_KNOWLEDGE = os.getenv("NORMALIZE_EXTRACTED_KNOWLEDGE", "False").lower() in ("true", "1", "t")
    CLEAN_EXTRACTED_KNOWLEDGE = os.getenv("CLEAN_EXTRACTED_KNOWLEDGE", "False").lower() in ("true", "1", "t")
    VALIDATE_EXTRACTED_KNOWLEDGE = os.getenv("VALIDATE_EXTRACTED_KNOWLEDGE", "False").lower() in ("true", "1", "t")
    REFINE_EXTRACTED_KNOWLEDGE = os.getenv("REFINE_EXTRACTED_KNOWLEDGE", "False").lower() in ("true", "1", "t")
    TOTAL_REFINEMENT_ITERATIONS = int(os.getenv("TOTAL_REFINEMENT_ITERATIONS", 2))

    # Evaluation Configuration
    REFLECTION_MODE = os.getenv("REFLECTION_MODE", "single")
    DEBATE_MAX_ITERATIONS = int(os.getenv("DEBATE_MAX_ITERATIONS", 3))
    JUDGE_num_retry = int(os.getenv("JUDGE_NUM_RETRY", 2))

    # Data Path Configuration
    SCHEMA_PATH = os.getenv("SCHEMA_PATH") or None
    SCIENTIFIC_DOCUMENT_PATH = os.getenv("SCIENTIFIC_DOCUMENT_PATH") or None
    FEW_SHOT_EXAMPLES_PATH = os.getenv("FEW_SHOT_EXAMPLES_PATH") or None

    # Results Output Path
    RESULTS_PATH = os.getenv("RESULTS_PATH") or None

    @staticmethod
    def validate_openai_api_key() -> bool:
        """
        Ensure OPENAI_API_KEY is set, else raise a clear error.
        Returns:
            bool: True if the API key is set.
        Raises:
            EnvironmentError: If OPENAI_API_KEY is not set.
        """
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise EnvironmentError("Missing OPENAI_API_KEY. Please set it in your environment:\n")
        return True
    
    @staticmethod
    def get_reflection_judge_models() -> list[str]:
        """
        Parse the REFLECTION_JUDGE_MODELS environment variable into a list of LLM strings.
        Expected format: 'PROVIDER1:model1,PROVIDER2:model2,...'
        Returns:
            list[str]: A list of LLM strings (e.g., ["OPENAI:gpt-4o", "SAIA:llama-3.3-70b"]).
        """
        models_str = os.getenv("REFLECTION_JUDGE_MODELS", "")
        return [item.strip() for item in models_str.split(",") if item.strip()]
    
    @staticmethod
    def get_reflection_critic_models() -> list[str]:
        """
        Parse the REFLECTION_CRITIC_MODELS environment variable into a list of LLM strings.
        Expected format: 'PROVIDER1:model1,PROVIDER2:model2,...'
        Returns:
            list[str]: A list of LLM strings (e.g., ["OPENAI:gpt-4o"]).
        """
        models_str = os.getenv("REFLECTION_CRITIC_MODELS", "")
        return [item.strip() for item in models_str.split(",") if item.strip()]
