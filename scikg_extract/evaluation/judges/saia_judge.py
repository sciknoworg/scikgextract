"""
SaiaJudge for evaluating extracted knowledge using the Saia model.

This module defines the SaiaJudge class, a subclass of BaseJudge, which uses the Saia model to evaluate the quality of the extracted knowledge based on the specified rubric and returns the score and feedback. It integrates with the SAIA adapter to format prompts and handle responses from the Saia model.
"""
# Python Imports
from types import SimpleNamespace

# SciKGExtract Model Imports
from scikg_extract.models.saia_adapter import SAIA_Adapter

# SciKGExtract Config Imports
from scikg_extract.config.process.processConfig import ProcessConfig

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.judges.base_judge import BaseJudge

# External Imports
from pydantic import BaseModel
from yescieval.base import Rubric

class SaiaJudge(BaseJudge):
    """
    SaiaJudge is a subclass of BaseJudge which uses the Saia model to evaluate the quality of the extracted knowledge based on the specified rubric and returns the score and feedback.
    """
    def __init__(self, model: str, temperature: float = 0.1, data_model: BaseModel = None) -> None:
        
        # Initialize the base Judge class
        super().__init__()

        # Saia model to use for judging
        self.model = model

        # Temperature for the Saia model
        self.temperature = temperature

        # Pydantic data model for validation
        self.data_model = data_model

        # Initialize the Saia adapter
        self.saia_adapter = SAIA_Adapter(model_name=model, temperature=temperature)

    def evaluate(self, rubric: Rubric) -> BaseModel:
        """
        Evaluates the given rubric using the Saia model and returns the evaluation results.
        Args:
            rubric (Rubric): The rubric containing the criteria for evaluation.
        Returns:
            BaseModel: The evaluation results mapped to the specified Pydantic data model.
        """

        try:
            # Initialize the logger
            logger = LogHandler.get_logger(__name__)
            logger.debug("Starting evaluation using SaiaJudge...")

            # Format the prompt template
            var_dict = {"process_name": ProcessConfig.Process_name, "process_description": ProcessConfig.Process_description, "scientific_article": rubric.scientific_article, "process_schema": rubric.process_schema, "extracted_data": rubric.extracted_data}

            # Encapsulating the System and User prompts to an object
            prompt_template = SimpleNamespace(
                system_prompt=rubric.system_prompt_template,
                user_prompt=rubric.user_prompt_template
            )
            
            # Define the evaluation function to be used with retry logic
            def _evaluate():
                return self.saia_adapter.structured_completion(prompt_template, var_dict, self.data_model)

            # Evaluate using the Saia adapter with retry logic
            return self._evaluate_with_retry(_evaluate, self.num_retry)
        except Exception as e:
            self.logger.debug(f"Exception Occurred while evaluating using SaiaJudge")
            self.logger.debug(f"Exception: {e}")
            return None