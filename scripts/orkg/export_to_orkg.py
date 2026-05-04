# Python Imports
import argparse

# External Imports
from orkg import Hosts

# Scikg_Extract Tool Imports
from scikg_extract.tools.knowledge_graph.orkg import validate_orkg_connection, materialize_template, get_orkg_connector

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

if __name__ == "__main__":

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Export ALD/E structured knowledge to ORKG.")
    parser.add_argument("--orkg_host", type=str, required=False, help="The ORKG host URL.")
    parser.add_argument("--orkg_email", type=str, required=False, help="The user's email for ORKG authentication.")
    parser.add_argument("--orkg_password", type=str, required=False, help="The user's password for ORKG authentication.")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Configure and Initialize the logger
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting export of ALD/E structured knowledge to ORKG...")

    # ORKG Host
    orkg_host = args.orkg_host if args.orkg_host else Hosts.PRODUCTION
    logger.info(f"Using ORKG host: {orkg_host}")

    # User Credentials
    orkg_email = args.orkg_email if args.orkg_email else "samirsamji@gmail.com"
    orkg_password = args.orkg_password if args.orkg_password else "Applebutton@159"
    logger.info(f"Using ORKG email: {orkg_email}")

    # Create ORKG connector
    orkg_connector = get_orkg_connector(orkg_host, orkg_email, orkg_password)
    logger.info("ORKG connector initialized.")

    # Validate ORKG connection
    valid_connection = validate_orkg_connection(orkg_connector)
    logger.info(f"ORKG connection valid: {valid_connection}")

    # Materialize template
    template_id = "R1434174"
    materialization_success = materialize_template(orkg_connector, template_id)
    logger.info(f"Template {template_id} materialization success: {materialization_success}")

    print(orkg_connector.templates.get_template_specifications(template_id))