"""
LangChain callback handler for per-iteration timing of the extraction workflow.

Hooks into the LangGraph/LangChain callback system to measure the wall-clock time spent in each tracked workflow node (extraction, reflection, feedback) per refinement iteration. Timings are logged and stored on the callback instance for downstream reporting.
"""
# Python Imports
import time

# External Library Imports
from langchain_core.callbacks import BaseCallbackHandler

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Dictionary to track the nodes we want to time in the workflow
TRACKED_NODES = {
    "extract_knowledge": "extraction",
    "validate_extracted_processes": "reflection",
    "provide_feedback": "feedback",
}

class IterationTimingCallback(BaseCallbackHandler):
    """
    A callback handler for tracking the time taken for each iteration of the extraction and refinement process in the knowledge extraction workflow. It logs the start and end time of each iteration and calculates the duration.
    """

    def __init__(self):
        """
        Initializes the callback handler with necessary data structures to track timings and iterations.
        """

        # Initialize the logger to log timing information
        self.logger = LogHandler.get_logger(__name__)

        # Run ID to node name mapping to track which node is being executed
        self._run_id_to_node: dict[str, str] = {}

        # Dictionary to track the start time of each node execution
        self._node_start_times: dict[str, float] = {}

        # Dictionary to track the current iteration's timings for extraction, reflection, and feedback
        self._current_iteration: dict[str, float] = {}

        # List to store the durations of each iteration for later analysis and summary logging
        self.iteration_durations: list[dict[str, float]] = []

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs) -> None:
        """
        Called when a chain starts. It checks if the node being executed is one of the tracked nodes and records the start time for that node.
        Args:
            **kwargs: Additional keyword arguments containing information about the chain execution, including the node name and run ID.
        """
        # Extract the node name from the keyword arguments and check if it's one of the tracked nodes
        node_name = kwargs.get("name", "")
        if node_name not in TRACKED_NODES:
            return
        
        # Record the start time for the node execution using the run ID to track which node is being executed
        run_id = str(kwargs.get("run_id", ""))
        self._run_id_to_node[run_id] = node_name
        self._node_start_times[node_name] = time.perf_counter()
        
        # New iteration starts with the extraction node
        if node_name == "extract_knowledge":
            self._current_iteration = {"extraction": 0.0, "reflection": 0.0, "feedback": 0.0}
            self.logger.debug(f"Iteration {len(self.iteration_durations) + 1} started.")

    def on_chain_end(self, outputs: dict, **kwargs) -> None:
        """
        Called when a chain finishes. It calculates the duration for the tracked nodes and logs it. If the feedback node finishes, it finalizes the iteration.
        Args:
            **kwargs: Additional keyword arguments containing information about the chain execution, including the node name and run ID.
        """
        # Extract the run ID and node name to identify which node has finished execution
        run_id = str(kwargs.get("run_id", ""))
        node_name = self._run_id_to_node.pop(run_id, None)
        if node_name not in TRACKED_NODES:
            return

        # Calculate the duration for the node execution and log it
        key = TRACKED_NODES[node_name]
        duration = time.perf_counter() - self._node_start_times.pop(node_name, time.perf_counter())
        self._current_iteration[key] = duration
        self.logger.debug(f"{key.capitalize()} node '{node_name}' completed in {duration:.2f} seconds.")

        # If the feedback node finishes, finalize the iteration by calculating the total duration and logging it
        if node_name == "provide_feedback":
            self._finalize_iteration()

    def on_chain_error(self, error: Exception, **kwargs) -> None:
        """
        Called when an error occurs in the chain execution. It logs the error and clears any stored timings for the current iteration to ensure accurate tracking for subsequent iterations.
        Args:
            error (Exception): The exception that occurred during chain execution.
            **kwargs: Additional keyword arguments containing information about the chain execution, including the run ID.
        """
        # Extract the run ID to identify which node had an error and clear any stored timings for that node and the current iteration
        run_id = str(kwargs.get("run_id", ""))
        node_name = self._run_id_to_node.pop(run_id, None)
        if node_name: self._node_start_times.pop(node_name, None)

        # Log the error that occurred during chain execution
        self.logger.error(f"Error in chain: {error}")

        # Clear the current iteration timings to ensure accurate tracking for subsequent iterations
        self._node_start_times.clear()

    def _finalize_iteration(self) -> None:
        """
        Finalizes the current iteration by calculating the total duration and logging it. This is called when the feedback node finishes.
        """
        # Calculate the total duration for the iteration by summing the durations of extraction, reflection, and feedback, and log the results
        total_duration = sum(self._current_iteration.values())
        self._current_iteration["total"] = total_duration

        # Store a copy of the current iteration durations
        self.iteration_durations.append(dict(self._current_iteration))

        # Log the summary of the iteration with the durations for extraction, reflection, feedback, and total time taken
        iteration_number = len(self.iteration_durations)
        self.logger.info(f"Iteration {iteration_number} completed | Extraction: {self._current_iteration['extraction']:.2f}s | Reflection: {self._current_iteration['reflection']:.2f}s | Feedback: {self._current_iteration['feedback']:.2f}s | Total: {total_duration:.2f}s"
        )

    def log_summary(self) -> None:
        """
        Logs a summary of all iterations with their respective durations.
        """
        # Log if no iterations were tracked
        if not self.iteration_durations:
            self.logger.info("No iterations to summarize.")
            return
        
        # Log the summary of all iterations with their respective durations for extraction, reflection, feedback, and total time taken
        self.logger.info("=== Iteration Timing Summary ===")
        for idx, iteration in enumerate(self.iteration_durations, start=1):
            self.logger.info(f"Iteration {idx} | Extraction: {iteration['extraction']:.2f}s | Reflection: {iteration['reflection']:.2f}s | Feedback: {iteration['feedback']:.2f}s | Total: {iteration['total']:.2f}s"
            )
        
        # Calculate and log the overall total time taken for all iterations
        overall_total = sum(iteration["total"] for iteration in self.iteration_durations)
        self.logger.info(f"Overall Total Time for {len(self.iteration_durations)} Iterations: {overall_total:.2f}s")
