class NormalizationConfig:
    """
    Configuration class for normalization of extracted data. Specifies different configuration to be used during the normalization step.
    """

    # Explicit properties paths to normalize
    include_paths: list[str] = [
        "aldSystem.aldMethod[*].compound",
        "aldSystem.materialDeposited",
        "reactantSelection.precursor[*].compound",
        "reactantSelection.precursor[*].precursor",
        "reactantSelection.coReactant[*].compound",
        "reactantSelection.coReactant[*].coReactant",
        "reactantSelection.carrierGas",
        "reactantSelection.purgingGas",
        "processParameters.substrate"
    ]

    # Explicit properties paths to exclude from normalization
    exclude_paths: list[str] = []

    # Manually curated Synonym to CID Mapping
    synonym_to_cid_mapping: dict = {}

    # PubChem LMDB Path
    pubchem_lmdb_path: str = ""