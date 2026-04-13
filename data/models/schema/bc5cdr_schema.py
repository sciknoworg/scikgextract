from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    """Semantic type of the entity."""
    CHEMICAL = 'Chemical'
    DISEASE = 'Disease'


class BC5CDREntity(BaseModel):
    """A chemical or disease named entity with a MeSH identifier."""
    model_config = ConfigDict(extra='forbid')

    text: str = Field(..., description='The entity mention text as it appears in the passage.')
    type: EntityType = Field(..., description='The semantic type of the entity.')
    identifier: str = Field(
        ..., description='MeSH identifier for the entity (e.g., D009270). Value is -1 when no MeSH mapping exists.'
    )
    offset: Optional[int] = Field(None, description='Character offset of the entity mention in the full document text.')
    length: Optional[int] = Field(None, description='Character length of the entity mention.')


class BC5CDRRelation(BaseModel):
    """A document-level Chemical-Induced-Disease (CID) relation."""
    model_config = ConfigDict(extra='forbid')

    type: str = Field('CID', description='The relation type. Always CID (Chemical-Induced-Disease).')
    chemical: str = Field(..., description='MeSH identifier of the chemical entity.')
    disease: str = Field(..., description='MeSH identifier of the disease entity.')


class BC5CDRSchema(BaseModel):
    """Schema for chemical and disease entity extraction and CID relation extraction from PubMed abstracts, based on the BioCreative V CDR dataset."""
    model_config = ConfigDict(extra='forbid')

    entities: List[BC5CDREntity] = Field(..., description='Chemical and disease named entities extracted from the text.')
    relations: List[BC5CDRRelation] = Field(
        ..., description='Document-level Chemical-Induced-Disease (CID) relations between a chemical and a disease.'
    )
