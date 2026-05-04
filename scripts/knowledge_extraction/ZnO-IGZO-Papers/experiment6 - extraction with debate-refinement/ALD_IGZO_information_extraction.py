"""
Script to extract and normalize structured IGZO ALD process information from scientific documents based on ALD experimental schema with Debate-Style Multi-Judge Refinement.
"""
# Python imports
import os
import argparse

# SciKGExtract utility imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, read_text_file, save_json_file

# SciKGExtract agent imports
from scikg_extract.agents.orchestrator_agent import orchestrate_extraction_workflow

# SciKGExtract config imports
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.agents.orchestrator import OrchestratorConfig
from scikg_extract.config.agents.workflow import WorkflowConfig
from scikg_extract.config.llm.llmConfig import ProviderRegistry

# SciKGExtract evaluation imports
from scikg_extract.evaluation.rubrics.informativeness import Completeness, Correctness

# Data Model for ALD Experimental Use Case
from data.models.schema.ALD_experimental_schema import ALDProcessList

if __name__ == "__main__":
    """Main function to extract ALD process information from scientific documents."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured ALD process information from scientific documents.")
    parser.add_argument("--extraction_llm", type=str, help="The name of the LLM to use for extraction in format 'provider:model_name' (e.g., 'OPENAI:gpt-4o').")
    parser.add_argument("--reflection_judge_llms", type=str, help="The names of the LLMs to use as judges for multi-judge refinement in format 'provider:model_name' separated by commas (e.g., 'OPENAI:gpt-4o,SAIA:meta-llama/llama-3.3-70b-instruct').")
    parser.add_argument("--reflection_critic_llms", type=str, help="The names of the LLMs to use as critics for multi-judge refinement in format 'provider:model_name' separated by commas (e.g., 'OPENAI:gpt-4o,SAIA:meta-llama/llama-3.3-70b-instruct').")
    parser.add_argument("--summarizer_llm", type=str, help="The name of the LLM to use for summarization in format 'provider:model_name' (e.g., 'OPENAI:gpt-4o').")
    parser.add_argument("--feedback_llm", type=str, help="The name of the LLM to use for feedback in format 'provider:model_name' (e.g., 'SAIA:meta-llama/llama-3.3-70b-instruct').")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--scientific_docs_dir", type=str, help="Directory containing scientific documents in text/markdown format.")

    # Parse the arguments
    args = parser.parse_args()

    # Build unique run identifier for concurrent execution (LLM name + PID)
    extraction_llm = args.extraction_llm if args.extraction_llm else "OPENAI:gpt-4o"
    run_id = f"{extraction_llm}_{os.getpid()}"

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=run_id)
    logger.info("Starting ALD information extraction script for IGZO with debate-style multi-judge refinement...")

    # Initialize the LLM model
    logger.info(f"Using LLM model: {extraction_llm}")

    # Initialize the Reflection Judge LLM models
    reflection_judge_llms = args.reflection_judge_llms if args.reflection_judge_llms else "OPENAI:gpt-5,SAIA:deepseek/deepseek-r1-0528"
    logger.info(f"Using Reflection Judge LLM models: {reflection_judge_llms}")

    # Initialize the Reflection Critic LLM models
    reflection_critic_llms = args.reflection_critic_llms if args.reflection_critic_llms else "SAIA:qwen/qwen3-30b-a3b-thinking-2507,SAIA:qwen/qwen3-30b-a3b-thinking-2507"
    logger.info(f"Using Reflection Critic LLM models: {reflection_critic_llms}")

    # Initialize the Summarizer LLM model
    summarizer_llm = args.summarizer_llm if args.summarizer_llm else "SAIA:mistralai/ministral-3b-2512"
    logger.info(f"Using Summarizer LLM model: {summarizer_llm}")

    # Initialize the Feedback LLM model
    feedback_llm = args.feedback_llm if args.feedback_llm else "SAIA:mistralai/ministral-3b-2512"
    logger.info(f"Using Feedback LLM model: {feedback_llm}")

    # Updating the process description for ALD
    ProcessConfig.Process_description = """
    Atomic Layer Deposition (ALD) is a thin-film fabrication technique that relies on sequential, self-limiting surface reactions to produce highly uniform and conformal coatings, even over complex 3D structures. In simulation use cases, ALD is modeled to understand how precursor chemistry, surface kinetics, temperature, and reactor flow dynamics influence film growth at the atomic scale. Simulations help predict growth-per-cycle, film uniformity, defect formation, and precursor diffusion behavior, enabling optimization of process parameters before physical experimentation. This accelerates materials development, reduces trial-and-error costs, and supports the design of advanced semiconductor, energy, and nanotechnology devices.

    In this extraction task, we are focusing on IGZO (Indium Gallium Zinc Oxide) thin film deposition via ALD. An IGZO ALD process is a supercycle-based thin-film deposition method used to form multicomponent oxide layers composed of indium oxide (In2O3), gallium oxide (Ga2O3), and zinc oxide (ZnO). The process deposits IGZO by sequentially repeating ALD sub-cycles of the individual metal oxides in a defined ratio. Each sub-cycle typically consists of a metal precursor pulse, a purge, an oxidant pulse (such as H2O, O3, or O2 plasma), and a second purge. A single IGZO supercycle is composed of a cycles of In2O3, b cycles of Ga2O3, and c cycles of ZnO, where the a:b:c ratio controls the IGZO film composition, electrical properties, and oxygen-vacancy concentration.

    Different precursors are used for each element. For example, diethylzinc (DEZ) and trimethylgallium (TMGa) are common for zinc and gallium, respectively, while a precursor like 3-(dimethylamino)propyl)dimethylindium (DADI) is used for indium. The goal of an IGZO ALD process is to produce a conformal, composition-controlled, amorphous IGZO film suitable for applications such as thin-film transistors (TFTs).
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Contraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else f"results/extractions/ZnO-IGZO-Papers/version6/experimental-usecase/IGZO/AtomicLimits Database"
    logger.info(f"Results Directory to save extracted data: {results_dir}")

    # Read the process schema from the JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/ALD/experimental-usecase/ALD-experimental-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/ALD/IGZO/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Directory containing scientific documents
    scientific_docs_dir = args.scientific_docs_dir if args.scientific_docs_dir else "data/research-papers/ALD/markdown/ZnO-IGZO-papers/experimental-usecase/IGZO/AtomicLimits Database"
    logger.info(f"Scientific Documents Directory: {scientific_docs_dir}")

    # Process each scientific document in the specified directory
    for root, _, filenames in os.walk(scientific_docs_dir):

        # Skip if no files found
        if not filenames: continue

        # Process each file in the directory
        for filename in filenames:
        
            # Process only markdown or text files
            if not filename.endswith(".md") and not filename.endswith(".txt"): 
                logger.debug(f"Skipping non-markdown/text file: {filename}")
                continue

            # Format the results directory path for the current document and JSON filename
            res_llm_model = ProviderRegistry.parse_llm_string(extraction_llm)[0].split("/")[-1]
            res_dir = f"{results_dir}{root.split(scientific_docs_dir)[-1].replace("\\", "/").strip()}/{res_llm_model}"
            json_filename = f"{os.path.splitext(filename)[0]}.json"

            # Check if the extraction result already exists
            if os.path.exists(f"{res_dir}/{json_filename}"):
                logger.info(f"Extraction result already exists for document: {filename}. Skipping extraction.")
                continue

            # Read the scientific document in markdown format
            logger.info(f"Processing scientific document: {filename}")
            scientific_document_filepath = f"{root}/{filename}"
            scientific_document = read_text_file(scientific_document_filepath)

            # Initialize orchestrator configuration
            orchestrator_config = OrchestratorConfig(
                extraction_llm=extraction_llm,
                process_schema=process_schema,
                scientific_document=scientific_document,
                examples=examples,
                extraction_data_model=ALDProcessList,
                reflection_judge_llms=reflection_judge_llms.split(","),
                reflection_critic_llms=reflection_critic_llms.split(","),
                summarizer_llm=summarizer_llm,
                rubrics=[Completeness, Correctness],
                feedback_llm=feedback_llm
            )

            # Initialize the Workflow configuration
            workflow_config = WorkflowConfig(
                normalize_extracted_data=False,
                clean_extracted_data=False,
                validate_extracted_data=True,
                refine_extracted_data=True,
                reflection_mode="debate",
                total_validation_retries=2
            )

            # Extract knowledge using the orchestrator agent
            final_state = orchestrate_extraction_workflow(orchestrator_config, workflow_config)
            logger.info(f"Extraction completed for document: {root}/{filename}")

            # Get the extracted knowledge from the final state
            extracted_knowledge = final_state["extracted_json"]

            # Save the extracted information to a JSON file
            file_saved = save_json_file(res_dir, json_filename, extracted_knowledge)
            if not file_saved: raise Exception(f"Failed to save extracted extracted information for document: {filename}")
            logger.info(f"extracted Extracted information saved to: {res_dir}/{json_filename}")