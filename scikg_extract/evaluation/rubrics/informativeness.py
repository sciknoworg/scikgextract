"""
Informativeness Rubrics for LLM-as-a-Judge evaluation of scientific information extraction.

Defines rubric classes for evaluating the informativeness of extracted structured knowledge, including Correctness (factual accuracy) and Completeness (coverage of relevant information). Each rubric class inherits from the Yescieval Rubric base class and implements the necessary methods for rendering papers, verbalizing criteria, and instructing the judge LLM.
"""
# SciKGExtract Prompts Imports
from scikg_extract.prompts.evaluation.rubrics import correctness
from scikg_extract.prompts.evaluation.rubrics import completeness

# Yescieval Rubric Base Class
from yescieval.base.rubric import Rubric

class Correctness(Rubric):
    """
    Correctness rubric for evaluating the factual accuracy of extracted structured knowledge against the source scientific document.
    """
    # Rubric Name
    name: str = "Correctness"
    
    # Scientific Article
    scientific_article: str

    # Process Schema in JSON format
    process_schema: dict

    # Structured Extracted Data in JSON format
    extracted_data: dict

    def __init__(self, scientific_article: str, process_schema: dict, extracted_data: dict) -> None:
        """
        Initializes the Correctness rubric with the specified system prompt, scientific article, process schema, and extracted data.
        Args:
            scientific_article (str): The scientific article used for evaluation.
            process_schema (dict): The process schema in JSON format.
            extracted_data (dict): The extracted structured data in JSON format.
        """
        super().__init__(
            name="Correctness",
            system_prompt_template=correctness.system_prompt, 
            papers={}, 
            question="", 
            answer="", 
            user_prompt_template=correctness.user_prompt,
            scientific_article=scientific_article,
            process_schema=process_schema,
            extracted_data=extracted_data
        )

    @staticmethod
    def get_rubric_name() -> str:
        return "Correctness"

    def render_papers(self) -> str:
        pass

    def verbalize(self) -> str:
        pass

    def instruct(self) -> list[dict[str, str]]:
        pass

class Completeness(Rubric):
    """
    Completeness rubric for evaluating the completeness of extracted structured knowledge against the source scientific document and process schema.
    """
    # Rubric Name
    name: str = "Completeness"

    # Scientific Article
    scientific_article: str

    # Process Schema in JSON format
    process_schema: dict

    # Structured Extracted Data in JSON format
    extracted_data: dict

    def __init__(self, scientific_article: str, process_schema: dict, extracted_data: dict) -> None:
        """
        Initializes the Completeness rubric with the specified system prompt, scientific article, process schema, and extracted data.
        Args:
            scientific_article (str): The scientific article used for evaluation.
            process_schema (dict): The process schema in JSON format.
            extracted_data (dict): The extracted structured data in JSON format.
        """
        super().__init__(
            name="Completeness",
            system_prompt_template=completeness.system_prompt, 
            papers={}, 
            question="", 
            answer="", 
            user_prompt_template=completeness.user_prompt,
            scientific_article=scientific_article,
            process_schema=process_schema,
            extracted_data=extracted_data
        )
    
    @staticmethod
    def get_rubric_name() -> str:
        return "Completeness"

    def render_papers(self) -> str:
        pass

    def verbalize(self) -> str:
        pass

    def instruct(self) -> list[dict[str, str]]:
        pass