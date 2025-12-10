# 📋 Overview

This directory contains various resources used in the SciKG-Extract project, including example extractions, gold-standard annotations, research papers, and JSON schema representations.

## 📁 Directory Structure

```
data/
├── examples/                   # Example extraction by domain-experts for LLM's assistance 
├── external/                   # External resources used in the project    
├── gold-standard-annotations/  # Domain-expert annotated data
├── models/                     # Pydantic models used in the project
│   ├── api/                    # API related Pydantic models
│   └── schema/                 # Schema related Pydantic models
├── research-papers/            # Research papers in PDF and Markdown formats
├── resources/                  # Resources used by the project
└── schemas/                    # JSON schema representations for scientific knowledge extraction
```

## 🚀 Usage

The resources in this directory are utilized by various components of the SciKG-Extract project to facilitate structured scientific knowledge extraction from literature. To execute the extraction process for any specific process, following are the recommendations for organizing your resources:

1. **Example Extractions**: Place example extraction files in the `examples/` directory. These files can be used to guide the LLM in understanding the expected extraction values.
2. **Gold-Standard Annotations**: Store domain-expert annotated files in the `gold-standard-annotations/` directory. These annotations serve as a benchmark for evaluating the performance of the extraction process.
3. **Models**: Create Pydantic models in the `models/` directory to define the structure of the different outputs expected from the extraction process.
4. **Research Papers**: Save research papers in the `research-papers/` directory in both PDF and Markdown formats for to be processed during extraction process.
5. **Resources**: Utilize the `resources/` directory for any additional resources required by the extraction process.
6. **Schemas**: Define JSON schema representations in the `schemas/` directory to outline the structure of the scientific knowledge to be extracted.

## 📄 ZnO and IGZO ALD Processes - Scientific Papers
The sub-directory `research-papers/ALD/pdf/ZnO-IGZO-papers/experimental-usecase/` contains details of scientific papers related to Atomic Layer Deposition (ALD) processes for Zinc Oxide (ZnO) and Indium Gallium Zinc Oxide (IGZO) from the AtomicLimits Database used during the experimentation phase of the SciKG-Extract Framework. These papers serve as the primary source of information for extracting structured scientific knowledge about the ALD processes of ZnO and IGZO materials.

Due to the closed-source nature of these papers, they are not included directly in the repository. For each category in ZnO and IGZO, a CSV file (papers_details.csv) is provided that contains metadata for each paper, including the title, authors and the DOI link. Users can access the full papers through the provided DOI links for their own analysis and extraction tasks.

The sub-directory is organized as follows:
1. `ZnO/`: Contains scientific papers related to the ALD process of Zinc Oxide (ZnO) from the AtomicLimits Database.
2. `IGZO/AtomicLimits Database/`: Contains scientific papers related to the ALD process of Indium Gallium Zinc Oxide (IGZO) from the AtomicLimits Database.
3. `IGZO/Others/`: Contains additional scientific papers related to IGZO that was provided by the domain experts.

> [!NOTE]
> The sub-directories containing the AtomicLimits Database papers are further organized/divided into folders based on the material, precursor and co-reactant used in the ALD process as per the AtomicLimits Database annotations.