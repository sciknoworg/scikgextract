from typing import List

from pydantic import BaseModel

class InformationItem(BaseModel):
    CID: int
    Synonym: List[str]

class InformationList(BaseModel):
    Information: List[InformationItem]

class PubChemSynonymsResponse(BaseModel):
    InformationList: InformationList