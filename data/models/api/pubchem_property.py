from typing import List

from pydantic import BaseModel

class PropertyItem(BaseModel):
    CID: int
    MolecularFormula: str
    IUPACName: str

class PropertyTable(BaseModel):
    Properties: List[PropertyItem]

class PubChemPropertyResponse(BaseModel):
    PropertyTable: PropertyTable