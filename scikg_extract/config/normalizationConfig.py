class NormalizationConfig:
    """
    Configuration for normalization of extracted data. Specifies which properties to include or exclude during normalization.
    """

    # Explicit paths to normalize
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

    # Explicit paths to exclude from normalization
    exclude_paths: list[str] = []