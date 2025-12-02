from types import SimpleNamespace

from scikg_extract.models.openai_adapter import Openai_Adapter
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.utils.log_handler import LogHandler

from pydantic import BaseModel
from yescieval.base.judge import Judge
from yescieval.base import Rubric

class OpenAIJudge(Judge):

    def __init__(self, model: str, temperature: float = 0.1, data_model: BaseModel = None) -> None:
        """
        Initializes the OpenAIJudge with the specified model and temperature.
        Args:
            model (str): The name of the OpenAI model to use for judging.
            temperature (float, optional): Sampling temperature for response generation. Defaults to 0.1.
            data_model (BaseModel, optional): The Pydantic data model for validation of the judged knowledge. Defaults to None.
        """
        
        # Initialize the base Judge class
        super().__init__()

        # OpenAI model to use for judging
        self.model = model

        # Temperature for the OpenAI model
        self.temperature = temperature

        # Pydantic data model for validation
        self.data_model = data_model

        # Initialize the OpenAI adapter
        self.openai_adapter = Openai_Adapter(model_name=model, temperature=temperature)

    def evaluate(self, rubric: Rubric) -> BaseModel:
        """
        Evaluates the given rubric using the OpenAI model and returns the evaluation results.
        Args:
            rubric (Rubric): The rubric containing the criteria for evaluation.
        Returns:
            BaseModel: The evaluation results mapped to the specified Pydantic data model.
        """
        # Initialize the logger
        logger = LogHandler.get_logger(__name__)
        logger.debug("Starting evaluation using OpenAIJudge...")

        # Format the prompt template
        var_dict = {"process_name": ProcessConfig.Process_name, "process_description": ProcessConfig.Process_description, "scientific_article": rubric.scientific_article, "process_schema": rubric.process_schema, "extracted_data": rubric.extracted_data}

        # Encapsulating the System and User prompts to an object
        prompt_template = SimpleNamespace(
            system_prompt=rubric.system_prompt_template,
            user_prompt=rubric.user_prompt_template
        )

        # Evaluate using the OpenAI adapter
        evaluation_result = self.openai_adapter.structured_completion(prompt_template, var_dict, self.data_model)

        # Return the evaluation result
        return evaluation_result