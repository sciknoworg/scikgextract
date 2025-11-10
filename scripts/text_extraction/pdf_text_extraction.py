import os
import logging
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions, PdfPipelineOptions, TableFormerMode, TableStructureOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode, DoclingDocument

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def parse_pdf(file_path: str) -> tuple[str, DoclingDocument]:
    """
    Parses a PDF file to extract text and tables using Docling library.

    Args:
        file_path (str): Path to the input PDF file.
    Returns:
        tuple[str, DoclingDocument]: A tuple containing the filename (without extension) and the extracted document object.
    Raises:
        AssertionError: If the specified file_path does not exist.  
    """
    # Check if file_path exists
    assert os.path.isfile(file_path), f"File {file_path} does not exist."

    # Initialize the Path Object
    pdf_path = Path(file_path)

    # Configure Docling PDF Pipeline Options
    pdf_options = PdfPipelineOptions(
        do_ocr=True,
        do_formula_enrichment=True,
        do_table_structure=True,
        table_structure_options=TableStructureOptions(do_cell_matching=True, mode=TableFormerMode.ACCURATE),
        generate_picture_images=True,
        accelerator_options=AcceleratorOptions(num_threads=4, device=AcceleratorDevice.AUTO)
    )

    # Initialize Docling Document Converter
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)}
    )

    # Parse the PDF
    parsed_document = converter.convert(source=pdf_path)
    document = parsed_document.document
    filename = parsed_document.input.file.stem

    # Return the filename and extracted document
    return filename, document

def export_as_markdown(document: DoclingDocument, filename: str, output_dir: str) -> None:
    """
    Exports the extracted document content to a Markdown file.

    Args:
        document (DoclingDocument): The extracted document object from Docling.
        filename (str): The base name for the output file (without extension).
        output_dir (str): Directory where the output Markdown file will be saved.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Define the output file path
    output_path = Path(output_dir) / f"{filename}.md"

    # Export the document to Markdown format
    with open(output_path, "w", encoding="utf-8") as md_file:
        md_file.write(document.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER))

if __name__ == "__main__":
    
    # PDF file path
    pdf_file_path = "data/research-papers/Atomic-layer-deposition/pdf/IGZO/Extra"

    # Output directory for Markdown files
    output_dir = "data/research-papers/Atomic-layer-deposition/markdown/IGZO/Extra"

    # Process each PDF file in the specified directory
    for filename in os.listdir(pdf_file_path):
        # Process only PDF files
        if not filename.lower().endswith(".pdf"): continue

        # Log the file being processed
        logging.info(f"Processing file: {filename}")
        
        # Full path to the PDF file
        file_path = os.path.join(pdf_file_path, filename)
        
        # Parse the PDF and extract content
        base_filename, extracted_document = parse_pdf(file_path)

        # Export the extracted content to Markdown
        export_as_markdown(extracted_document, base_filename, output_dir)