"""
OllamaJudge class for evaluating extracted structured knowledge using an OLLAMA model.

The OllamaJudge class inherits from the BaseJudge and implements the evaluate method to use an OLLAMA model for scoring the quality of the extracted knowledge based on a given rubric. It formats the prompts according to the rubric's templates, invokes the OLLAMA adapter, and includes retry logic for robustness.
"""
# Python Imports
from types import SimpleNamespace

# SciKGExtract Model Imports
from scikg_extract.models.ollama_adapter import OLLAMA_Adapter

# SciKGExtract Config Imports
from scikg_extract.config.process.processConfig import ProcessConfig

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.judges.base_judge import BaseJudge

# External Imports
from pydantic import BaseModel
from yescieval.base import Rubric

class OllamaJudge(BaseJudge):
    """
    OllamaJudge is a subclass of BaseJudge which uses an OLLAMA model to evaluate the quality of the extracted structured knowledge based on the specified rubric and return a score.
    """
    def __init__(self, model: str, temperature: float = 0.1, data_model: BaseModel = None) -> None:
        
        # Initialize the base Judge class
        super().__init__()

        # Ollama model to use for judging
        self.model = model

        # Temperature for the Ollama model
        self.temperature = temperature

        # Pydantic data model for validation
        self.data_model = data_model

        # Initialize the Ollama adapter
        self.ollama_adapter = OLLAMA_Adapter(model_name=model, temperature=temperature)

    def evaluate(self, rubric: Rubric) -> BaseModel:
        """
        Evaluates the extracted structured knowledge against the specified rubric using the Ollama model. Returns a score or evaluation result based on the rubric's criteria.
        Args:
            rubric (Rubric): The evaluation rubric containing the criteria and prompts for judging the extraction quality.
        Returns:
            BaseModel: The evaluation result, typically containing a score or structured feedback based on the rubric.
        """
        try:
            # Initialize the logger
            logger = LogHandler.get_logger(__name__)
            logger.debug("Starting evaluation using OllamaJudge...")

            # Format the prompt template
            var_dict = {"process_name": ProcessConfig.Process_name, "process_description": ProcessConfig.Process_description, "scientific_article": rubric.scientific_article, "process_schema": rubric.process_schema, "extracted_data": rubric.extracted_data}

            # Encapsulating the System and User prompts to an object
            prompt_template = SimpleNamespace(
                system_prompt=rubric.system_prompt_template,
                user_prompt=rubric.user_prompt_template
            )

            # Define the evaluation function to be used with retry logic
            def _evaluate():
                return self.ollama_adapter.structured_completion(prompt_template, var_dict, self.data_model)

            # Evaluate using the Ollama adapter with retry logic
            return self._evaluate_with_retry(_evaluate, self.num_retry)
        except Exception as e:
            self.logger.debug(f"Exception Occurred while evaluating using OllamaJudge")
            self.logger.debug(f"Exception: {e}")
            return None