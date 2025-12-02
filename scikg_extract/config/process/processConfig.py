class ProcessConfig:
    """
    Configuration class for defining the process details used in knowledge extraction.
    """
    
    # Process Name
    Process_name = "Atomic Layer Deposition"

    # Process Description
    Process_description = """
    Atomic layer deposition (ALD) is a surface-controlled thin film deposition technique that can enable ultimate control over the film thickness, uniformity on large-area substrates and conformality on 3D (nano)structures. Each ALD cycle consists at least two half-cycles (but can be more complex), containing a precursor dose step and a co-reactant exposure step, separated by purge or pump steps. Ideally the same amount of material is deposited in each cycle, due to the self-limiting nature of the reactions of the precursor and co-reactant with the surface groups on the substrate. By carrying out a certain number of ALD cycles, the targeted film thickness can be obtained.
    """

    # Process property constraints
    Process_property_constraints = """
    1. ALD process:
    -Use ALD process names exactly as written in the paper.
    -You may assign Thermal ALD, Plasma-enhanced ALD (PEALD), or Spatial ALD (SALD) only when clearly supported by reactant or process evidence (H₂O or other, plasma present, or spatial configuration).
    -Do not invent or infer any other ALD names (e.g., FEBALD, LEALD).
    -If uncertain, leave the ALDMethod unspecified.

    2. Material deposited:
    -Extract only data related to the requested material (e.g. ZnO).
    -If not specifically asked, exclude doped versions, alloys, or composite materials (e.g. Al:ZnO, Ga:ZnO, InGaZnO).
    -Exclude ALD data for other materials mentioned in the same paper (e.g. TiO₂, In₂O₃), unless explicitly requested.
    -If data is reported for a process sequence depositing multiple films, only retain information related to the target material's deposition conditions.
    
    3. Co-reactant:
    -When identifying co-reactants, ensure they are chemically correct for the deposited material. (e.g. For ZnO, only extract oxygen-containing co-reactants (e.g. H₂O, O₂ plasma, O₃, H₂O₂, O₂, N₂O))
    -If multiple co-reactants are listed, only extract those explicitly used for the target material's ALD process.
    """
