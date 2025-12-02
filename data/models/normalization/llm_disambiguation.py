from pydantic import BaseModel

class LLM_Disambiguation(BaseModel):
    """
    LLM_Disambiguation is a Pydantic model that holds the disambiguated chemical name(s) returned by the LLM.
    """

    original_value: str
    InChI: str
    InChIKey: str
    SMILES: str
    Molecular_Formula: str