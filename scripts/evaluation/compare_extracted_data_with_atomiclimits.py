import os
import json
import argparse

from rapidfuzz import fuzz
from sklearn.metrics import precision_score, recall_score, f1_score

from scikg_extract.utils.evaluation_utils import bert_score, cosine_similarity_score
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file

if __name__ == "__main__":
    
    # Configure argument parser
    parser = argparse.ArgumentParser(description="Compare extracted data values with AtomicLimits database annotations.")
    parser.add_argument("--input", type=str, required=False, help="Path to the directory containing extracted JSON files.")
    parser.add_argument("--output", type=str, required=False, help="Path to save the comparison results.")
    parser.add_argument("--key", type=str, default="processes", help="Key containing nested JSON data to compare.")
    parser.add_argument("--llm_model", type=str, default="gpt-5-mini", help="The name of the large language model used during extraction.")

    # Parse arguments
    args = parser.parse_args()

    # Initialize logger
    logger = LogHandler.setup_module_logging("compare_extracted_data_with_atomiclimits")
    logger.info("Starting comparison of extracted data with AtomicLimits database...")

    # Input Path
    input_path = args.input if args.input else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version2/IGZO/AtomicLimits Database"
    logger.info(f"Input Path: {input_path}")

    # LLM Model used in extraction
    llm_model = args.llm_model if args.llm_model else "gpt-5-mini"
    logger.info(f"LLM Model used: {llm_model}")

    # Output Path
    output_path = args.output if args.output else f"results/statistics/atomic-layer-deposition/experimental-usecase/version1/IGZO/comparison_IGZO_AtomicLimits_{llm_model}.xlsx"
    logger.info(f"Output Path: {output_path}")

    # Evaluate with or without normalization
    evaluate_with_normalization = True

    # Initialize dictionary to hold 
    comparison_results = {
        "material_deposited": {"reference": [], "predicted": []},
        "precursor": {"reference": [], "predicted": []},
        "coreactant1": {"reference": [], "predicted": []},
        "coreactant2": {"reference": [], "predicted": []},
        "coreactant3": {"reference": [], "predicted": []}
    }

    # Initialize CID mapping for atomicLimits annotations
    cid_mapping = {
        "GaMe3": "15051", 
        "ZnEt2": "101667988", 
        "O2 plasma": "977", 
        "O3": "24823", 
        "InCp": "85843794", 
        "InEt3": "101912", 
        "GaEt3": "66198", 
        "InMe3": "76919", 
        "H2O": "962",
        "H2O2": "784",
        "Zn": "23994",
        "O2": "977",
        "Zn(acac)2": "56846320",
        "Zn(OAc)2": "11192",
        "ZnCl2": "5727",
        "EtOH": "702",
        "H2O photo assisted": "962",
        "H2O plasma": "962",
        "H2O+ NH3": "962, 222",
        "H2O+ NH3 + O2": "962, 977, 222",
        "N2O": "948",
        "N2O plasma": "948",
        "ZnMe2": "11010",
        "ZnO": "14806"
    }

    # Iterate over JSON files in the input directory
    for root, _, files in os.walk(input_path):
        
        # Skipping if no files found
        if not files: continue

        # Check if all files are JSON
        if not all(file.endswith(".json") for file in files): continue

        # Extracting AtomicLimits annotation from directory structure and LLM model
        atomiclimits_annotation, llm = root.split(os.sep)[-2:]
        
        # Skip if LLM model does not match
        if llm != llm_model: continue
        logger.debug(f"Processing AtomicLimits Annotation: {atomiclimits_annotation}, LLM Model: {llm}")

        # Format the AtomicLimits annotation
        atomiclimits_annotation = atomiclimits_annotation.split(" - ")
        logger.debug(f"Formatted AtomicLimits Annotation: {atomiclimits_annotation}")

        # Iterate over files
        for file in files:

            logger.info(f"Processing file: {file}")

            # Read the JSON file
            file_path = os.path.join(root, file)
            json_data = read_json_file(file_path)
            json_data = json_data.get(args.key, json_data) if args.key else json_data
            logger.debug(f"Processing file: {file_path} with {len(json_data)} entries.")

            # Iterate over each process entry in the JSON data
            for index, process in enumerate(json_data):
                logger.debug(f"Processing entry: {index + 1}")

                # Extract material deposited
                material_deposited_atmoiclimits = "IGZO" # Since we are in ZnO directory
                
                # Append CID if available
                if evaluate_with_normalization and material_deposited_atmoiclimits in cid_mapping:
                    material_deposited_atmoiclimits = f"{material_deposited_atmoiclimits} [CID:{cid_mapping[material_deposited_atmoiclimits]}]"

                material_deposited = process.get("aldSystem", {}).get("materialDeposited", "")

                if evaluate_with_normalization and material_deposited_atmoiclimits and material_deposited:

                    # Format the predicted material deposited
                    if material_deposited["sameAs"]:
                        material_deposited = f"{material_deposited["value"]} [CID:{", ".join([cid.split("/")[-1] for cid in material_deposited["sameAs"]])}]"
                    else:
                        material_deposited = material_deposited["value"]

                comparison_results["material_deposited"]["reference"].append(material_deposited_atmoiclimits)
                comparison_results["material_deposited"]["predicted"].append(material_deposited)

                # Extract precursor
                precursor_atmoiclimits = atomiclimits_annotation[0] if len(atomiclimits_annotation) > 1 else ""

                # Append CID if available
                if evaluate_with_normalization and precursor_atmoiclimits in cid_mapping:
                    precursor_atmoiclimits = f"{precursor_atmoiclimits} [CID:{cid_mapping[precursor_atmoiclimits]}]"

                precursor = process.get("reactantSelection", {}).get("precursor", [])

                # Iterate over precursor list
                for prec in precursor:
                    prec_cid = prec.get("precursor", "")
                    
                    if evaluate_with_normalization:
                        if prec.get("precursor", {}).get("sameAs", []):
                            prec_cid = f"{prec.get("precursor", {}).get("value", "")} [CID:{", ".join([cid.split("/")[-1] for cid in prec.get("precursor", {}).get("sameAs", [])])}]"
                        else:
                            prec_cid = prec.get("precursor", {}).get("value", "")

                    if precursor_atmoiclimits and prec_cid:
                        comparison_results["precursor"]["reference"].append(precursor_atmoiclimits)
                        comparison_results["precursor"]["predicted"].append(prec_cid)

                # Extract coreactant1
                coreactant1_atmoiclimits = atomiclimits_annotation[1] if len(atomiclimits_annotation) >= 2 else ""

                # Append CID if available
                if evaluate_with_normalization and coreactant1_atmoiclimits in cid_mapping:
                    coreactant1_atmoiclimits = f"{coreactant1_atmoiclimits} [CID:{cid_mapping[coreactant1_atmoiclimits]}]"

                coreactant1 = process.get("reactantSelection", {}).get("coReactant", [])
                
                coreactant1 = "" if not coreactant1 else coreactant1[0].get("coReactant", "")
                if evaluate_with_normalization and coreactant1_atmoiclimits and coreactant1:

                    # Format the predicted coreactant1
                    if coreactant1["sameAs"]:
                        coreactant1 = f"{coreactant1["value"]} [CID:{', '.join([cid.split('/')[-1] for cid in coreactant1["sameAs"]])}]"
                    else:
                        coreactant1 = coreactant1["value"]

                comparison_results["coreactant1"]["reference"].append(coreactant1_atmoiclimits)
                comparison_results["coreactant1"]["predicted"].append(coreactant1)

                # Extract coreactant2
                coreactant2_atmoiclimits = atomiclimits_annotation[2] if len(atomiclimits_annotation) >= 3 else ""

                # Append CID if available
                if evaluate_with_normalization and coreactant2_atmoiclimits in cid_mapping:
                    coreactant2_atmoiclimits = f"{coreactant2_atmoiclimits} [CID:{cid_mapping[coreactant2_atmoiclimits]}]"

                coreactant2 = process.get("reactantSelection", {}).get("coReactant", [])
                coreactant2 = "" if not coreactant2 or len(coreactant2) < 2 else coreactant2[1].get("coReactant", "")
                if evaluate_with_normalization and coreactant2_atmoiclimits and coreactant2:

                    # Format the predicted coreactant2
                    if coreactant2["sameAs"]:
                        coreactant2 = f"{coreactant2["value"]} [CID:{', '.join([cid.split('/')[-1] for cid in coreactant2["sameAs"]])}]"
                    else:
                        coreactant2 = coreactant2["value"]

                comparison_results["coreactant2"]["reference"].append(coreactant2_atmoiclimits)
                comparison_results["coreactant2"]["predicted"].append(coreactant2)

                # Extract coreactant3
                coreactant3_atmoiclimits = atomiclimits_annotation[3] if len(atomiclimits_annotation) >= 4 else ""

                # Append CID if available
                if evaluate_with_normalization and coreactant3_atmoiclimits in cid_mapping:
                    coreactant3_atmoiclimits = f"{coreactant3_atmoiclimits} [CID:{cid_mapping[coreactant3_atmoiclimits]}]"

                coreactant3 = process.get("reactantSelection", {}).get("coReactant", [])
                coreactant3 = "" if not coreactant3 or len(coreactant3) < 3 else coreactant3[2].get("coReactant", "")
                if evaluate_with_normalization and coreactant3_atmoiclimits and coreactant3:

                    # Format the predicted coreactant3
                    if coreactant3["sameAs"]:   
                        coreactant3 = f"{coreactant3["value"]} [CID:{', '.join([cid.split('/')[-1] for cid in coreactant3["sameAs"]])}]"
                    else:
                        coreactant3 = coreactant3["value"]

                comparison_results["coreactant3"]["reference"].append(coreactant3_atmoiclimits)
                comparison_results["coreactant3"]["predicted"].append(coreactant3)

    # Compute evaluation metrics for each field
    for field, data in comparison_results.items():
        
        # Extract references and predictions
        references = data["reference"]
        predictions = data["predicted"]

        # Skip if no data
        if not references or not predictions: continue

        # Calculate exact match accuracy
        exact_matches = sum(1 for ref, pred in zip(references, predictions) if ref == pred)
        accuracy = exact_matches / len(references)
        print(f"Exact Match Accuracy for {field}: {accuracy:.4%}")

        # Calculate the Cosine Similarity score
        cosine_results = cosine_similarity_score(references, predictions, embedding_model="allenai/scibert_scivocab_uncased", max_length=512)
        print(f"Cosine Similarity scores for {field}: {cosine_results}")

        # Calculate BERT score
        bert_results = bert_score(references, predictions, embedding_model="allenai/scibert_scivocab_uncased", embedding_model_revision="24f92d32b1bfb0bcaf9ab193ff3ad01e87732fc1")
        print(f"BERT scores for {field}: {bert_results}")

        # Calculate the recall, precision and F1-score on CIDs
        cid_references = []
        cid_predictions = []

        for ref, pred in zip(references, predictions):
            # Check which has highest number of CIDs
            ref_cids = set([cid.strip() for cid in ref.split("[CID:")[-1].rstrip("]").split(",")]) if "[CID:" in ref else set([""])
            pred_cids = set([cid.strip() for cid in pred.split("[CID:")[-1].rstrip("]").split(",")]) if "[CID:" in pred else set([""])
            highest_cid_count = max(len(ref_cids), len(pred_cids))

            # Append to list with duplicates for multiple CIDs
            cid_references.extend(list(ref_cids) * highest_cid_count if len(ref_cids) < len(pred_cids) else list(ref_cids))
            cid_predictions.extend(list(pred_cids) * highest_cid_count if len(pred_cids) < len(ref_cids) else list(pred_cids))
        
        precision = precision_score(cid_references, cid_predictions, average='weighted', zero_division=0)
        recall = recall_score(cid_references, cid_predictions, average='weighted', zero_division=0)
        f1 = f1_score(cid_references, cid_predictions, average='weighted', zero_division=0)

        print(f"Precision for {field}: {precision:.4%}, Recall: {recall:.4%}, F1-score: {f1:.4%}")