# 📋 Overview

We present here multiple Jupyter notebooks that demonstrate different functionalities and aspects of the SciKGExtract framework. Each notebook is designed to guide users through specific tasks, functionalities, and analysis related to scientific knowledge extraction using SciKGExtract. Additionally, all these notebooks are developed on the Atomic Layer Deposition (ALD) domain as a test case, but can be adapted to other scientific domains as well.

## 📚 Notebooks Organization
The notebooks are organized as follows:
1. **Tutorial Notebooks**: These notebooks provide step-by-step tutorials on various functionalities of SciKGExtract, including knowledge extraction, normalization, reflection, and refinement.
   - [01_SciKGExtract_Knowledge_Extraction.ipynb](tutorials/01_SciKGExtract_Knowledge_Extraction.ipynb): Demonstrates the structured knowledge extraction process from scientific texts.
   - [02_SciKGExtract_Knowledge_Extraction_Normalization.ipynb](tutorials/02_SciKGExtract_Knowledge_Extraction_Normalization.ipynb): Demonstrates the structured knowledge extraction together with normalization of extracted entities, particularly chemical entities.
   - [03_SciKGExtract_Knowledge_Extraction_Normalization_Reflection.ipynb](tutorials/03_SciKGExtract_Knowledge_Extraction_Normalization_Reflection.ipynb): Covers the reflection and evaluation of the extracted and normalized knowledge.

2. **Analysis Notebooks**: These notebooks focuses on analyzing results, and insights derived from the extraction process.
    - [01_ZnO_and_IGZO_data_analysis.ipynb](analysis/01_ZnO_and_IGZO_data_analysis.ipynb): Analyzes using different graph-based techniques, the extracted knowledge specifically for ZnO and IGZO ALD processes to derive insights about different process properties.
    - [02_ZnO_IGZO_normalization_analysis](analysis/02_ZnO_IGZO_normalization_analysis.ipynb): Analyzes the normalization results specifically for ZnO and IGZO ALD processes to visualize different chemical entities and their normalized identifiers.

3. **Evaluation Notebooks**: These notebooks focuses on different evaluation metrics to assess the quality of the extracted knowledge with a reference annotated dataset.
    - [01_ZnO_and_IGZO_quantitative_evaluations.ipynb](evaluation/01_ZnO_and_IGZO_quantitative_evaluations.ipynb): Shows different quantitative evaluation metrics to assess the quality of the extracted knowledge for ZnO and IGZO ALD processes against a reference annotated dataset.