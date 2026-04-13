from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    """Semantic type of a biomedical entity."""
    GENE_OR_GENE_PRODUCT = 'GeneOrGeneProduct'
    DISEASE_OR_PHENOTYPIC_FEATURE = 'DiseaseOrPhenotypicFeature'
    CHEMICAL_ENTITY = 'ChemicalEntity'
    SEQUENCE_VARIANT = 'SequenceVariant'
    ORGANISM_TAXON = 'OrganismTaxon'
    CELL_LINE = 'CellLine'


class RelationType(str, Enum):
    """Semantic relation type between two biomedical entities."""
    ASSOCIATION = 'Association'
    POSITIVE_CORRELATION = 'Positive_Correlation'
    NEGATIVE_CORRELATION = 'Negative_Correlation'
    BIND = 'Bind'
    COMPARISON = 'Comparison'
    CONVERSION = 'Conversion'
    COTREATMENT = 'Cotreatment'
    DRUG_INTERACTION = 'Drug_Interaction'


class BioREDEntity(BaseModel):
    """A biomedical named entity with a database identifier."""
    model_config = ConfigDict(extra='forbid')

    text: str = Field(..., description='The entity mention text as it appears in the passage.')
    type: EntityType = Field(..., description='The semantic type of the entity.')
    identifier: str = Field(..., description='Database identifier (e.g., MeSH ID, NCBI Gene ID, NCBI Taxonomy ID).')
    offset: Optional[int] = Field(None, description='Character offset of the entity mention in the full document text.')
    length: Optional[int] = Field(None, description='Character length of the entity mention.')


class BioREDRelation(BaseModel):
    """A document-level relation between two biomedical entities, identified by their database identifiers."""
    model_config = ConfigDict(extra='forbid')

    type: RelationType = Field(..., description='The semantic relation type between the two entities.')
    entity1: str = Field(..., description='Database identifier of the first entity.')
    entity2: str = Field(..., description='Database identifier of the second entity.')
    novel: bool = Field(..., description='Whether this relation is novel (not previously reported in the literature).')


class BioREDSchema(BaseModel):
    """Schema for biomedical entity and relation extraction from PubMed abstracts, based on the BioRED dataset."""
    model_config = ConfigDict(extra='forbid')

    entities: List[BioREDEntity] = Field(..., description='Biomedical named entities extracted from the text.')
    relations: List[BioREDRelation] = Field(
        ..., description='Document-level relations between entity pairs, identified by their database identifiers.'
    )
