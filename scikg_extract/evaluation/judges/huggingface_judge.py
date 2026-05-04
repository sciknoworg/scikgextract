"""
HuggingFaceJudge for evaluating structured knowledge extraction using HuggingFace models.

Implements the BaseJudge interface to evaluate extracted data against specified rubrics using a HuggingFace model. The judge formats the evaluation prompt, calls the HuggingFace_Adapter to get the model's response, and parses it into a structured evaluation rating based on a provided Pydantic data model.
"""
# Python Imports
from types import SimpleNamespace

# SciKGExtract Model Imports
from scikg_extract.models.huggingface_adapter import HuggingFace_Adapter

# SciKGExtract Config Imports
from scikg_extract.config.process.processConfig import ProcessConfig

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.judges.base_judge import BaseJudge

# External Imports
from pydantic import BaseModel
from yescieval.base import Rubric

class HuggingFaceJudge(BaseJudge):
    """
    HuggingFaceJudge implements the BaseJudge interface for evaluating structured knowledge extraction using HuggingFace models. It uses the HuggingFace_Adapter to call a specified HuggingFace model.
    """

    def __init__(self, model: str, temperature: float = 0.1, data_model: BaseModel = None) -> None:
        
        # Initialize the base Judge class
        super().__init__()

        # HuggingFace model to use for judging
        self.model = model

        # Temperature for the HuggingFace model
        self.temperature = temperature

        # Pydantic data model for validation
        self.data_model = data_model

        # Initialize the HuggingFace adapter
        self.huggingface_adapter = HuggingFace_Adapter(model_name=model, temperature=temperature)

    def evaluate(self, rubric: Rubric) -> BaseModel:
        """
        Evaluates the extracted data against the provided rubric using the HuggingFace model. Returns a structured evaluation rating based on the specified data model.
        Args:
            rubric (Rubric): The evaluation rubric containing the scientific article, process schema, extracted data, and prompt templates.
        Returns:
            BaseModel: A structured evaluation rating parsed from the HuggingFace model's response, or None if evaluation fails.
        """
        try:
            # Initialize the logger
            logger = LogHandler.get_logger(__name__)
            logger.debug("Starting evaluation using HuggingFaceJudge...")

            # Format the prompt template
            var_dict = {"process_name": ProcessConfig.Process_name, "process_description": ProcessConfig.Process_description, "scientific_article": rubric.scientific_article, "process_schema": rubric.process_schema, "extracted_data": rubric.extracted_data}

            # Encapsulating the System and User prompts to an object
            prompt_template = SimpleNamespace(
                system_prompt=rubric.system_prompt_template,
                user_prompt=rubric.user_prompt_template
            )

            # Define the evaluation function to be used with retry logic
            def _evaluate():
                return self.huggingface_adapter.structured_completion(prompt_template, var_dict, self.data_model)

            # Evaluate using the HuggingFace adapter with retry logic
            return self._evaluate_with_retry(_evaluate, self.num_retry)
        except Exception as e:
            self.logger.debug(f"Exception Occurred while evaluating using HuggingFaceJudge")
            self.logger.debug(f"Exception: {e}")
            return None