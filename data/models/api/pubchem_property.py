from typing import List, Optional

from pydantic import BaseModel

class PropertyItem(BaseModel):
    CID: int
    MolecularFormula: Optional[str] = None
    IUPACName: Optional[str] = None
    ConnectivitySMILES: Optional[str] = None
    CanonicalSMILES: Optional[str] = None
    InChIKey: Optional[str] = None

class PropertyTable(BaseModel):
    Properties: List[PropertyItem]

class PubChemPropertyResponse(BaseModel):
    PropertyTable: PropertyTable