"""
BaseJudge class extending yescieval's Judge with retry logic and exception handling.

This module defines the BaseJudge class, which extends the Judge class from the yescieval library. The BaseJudge implements retry logic and exception handling for the evaluate method, allowing for more resilient evaluation calls in the LLM-as-a-Judge paradigm. The _evaluate_with_retry helper method is used to invoke evaluation functions with a specified number of retries before raising a RuntimeError.
"""
# Python Imports
from typing import Any

# External Imports
from yescieval.base.judge import Judge

# SciKGExtract Config Imports
from scikg_extract.config.llm.envConfig import EnvConfig

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

class BaseJudge(Judge):
    """
    BaseJudge extends the yescieval Judge with retry logic and exception handling for resilient evaluation calls.
    """

    def __init__(self, num_retry: int = None) -> None:
        """
        Initializes the BaseJudge.
        Args:
            num_retry (int, optional): Maximum number of retry attempts for evaluate calls. Defaults to the JUDGE_num_retry value from EnvConfig.
        """
        super().__init__()
        self.num_retry = num_retry if num_retry else EnvConfig.JUDGE_num_retry
        self.logger = LogHandler.get_logger(__name__)

    def _evaluate_with_retry(self, evaluate_func, max_retries: int) -> Any | None:
        """
        Helper method to invoke an evaluation function with retry logic. Raises RuntimeError after maximum retries are exhausted.
        Args:
            evaluate_func: The function to be invoked with retry logic.
            max_retries (int): The maximum number of retries allowed.
        Returns:
            Any | None: The output from the invoked function, or None if no response is obtained after retries.
        Raises:
            RuntimeError: If the maximum number of retries is exhausted without obtaining a response.
        """
        retries = 0
        while retries < max_retries:
            try:
                return evaluate_func()
            except Exception as e:
                self.logger.debug(f"Exception occurred during evaluation: {e}")
                retries += 1
                self.logger.debug(f"Retrying evaluation... Attempt {retries}/{max_retries}")
        self.logger.debug(f"Maximum evaluation retries exhausted.")
        raise RuntimeError(f"Maximum evaluation retries exhausted.")
