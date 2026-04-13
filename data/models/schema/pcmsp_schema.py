from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class MaterialSubtype(str, Enum):
    """Material subtype: target (final product), recipe (starting material), intermedium (intermediate product), or others."""
    TARGET = 'Material-target'
    RECIPE = 'Material-recipe'
    INTERMEDIUM = 'Material-intermedium'
    OTHERS = 'Material-others'


class PropertySubtype(str, Enum):
    """Property subtype for measured process properties."""
    TEMPERATURE = 'Property-temperature'
    TIME = 'Property-time'
    PRESSURE = 'Property-pressure'
    RATE = 'Property-rate'


class RelationType(str, Enum):
    """Typed directed relation types between entities."""
    DESCRIPTOR_OF = 'Descriptor-of'
    VALUE_OF = 'Value-of'
    BRAND_OF = 'Brand-of'
    CONDITION_OF = 'Condition-of'
    PARTICIPANT_MATERIAL = 'Participant-material'
    DEVICE_OF_OPERATION = 'Device-of-operation'
    NEXT_OPERATION = 'Next-operation'
    COREFERENCE = 'Coreference'


class Material(BaseModel):
    """A material entity with a subtype qualifier."""
    model_config = ConfigDict(extra='forbid')

    text: str = Field(..., description='The material mention text (e.g., Li1.1Cu0.9S, CuS).')
    subtype: MaterialSubtype = Field(
        ..., description='Material subtype: target (final product), recipe (starting material), intermedium (intermediate product), or others.'
    )


class Property(BaseModel):
    """A measured property entity with a subtype qualifier."""
    model_config = ConfigDict(extra='forbid')

    text: str = Field(..., description='The property mention text (e.g., 900 °C, 10 h, 5 MPa).')
    subtype: PropertySubtype = Field(..., description='Property subtype.')


class PcMSPEntities(BaseModel):
    """Named entities extracted from materials synthesis procedure text."""
    model_config = ConfigDict(extra='forbid')

    materials: List[Material] = Field(..., description='Materials mentioned in the text, each with a subtype.')
    operations: List[str] = Field(..., description='Synthesis operations or process steps (e.g., obtained, pressed, annealed).')
    descriptors: List[str] = Field(..., description='Qualitative descriptors of entities (e.g., polycrystalline, anhydrous, powder).')
    values: List[str] = Field(..., description='Quantitative values with units (e.g., 99.999%, 14 mm, 1 : 1 stoichiometry).')
    properties: List[Property] = Field(..., description='Measured properties, each with a subtype.')
    devices: List[str] = Field(..., description='Equipment or apparatus used (e.g., Al2O3 tubes, furnace).')
    brands: List[str] = Field(..., description='Manufacturer or supplier names (e.g., Sigma Aldrich).')


class PcMSPRelation(BaseModel):
    """A typed directed relation between a source and target entity."""
    model_config = ConfigDict(extra='forbid')

    type: RelationType = Field(..., description='The relation type linking source to target.')
    source: str = Field(..., description='The source entity text.')
    target: str = Field(..., description='The target entity text.')


class PcMSPSchema(BaseModel):
    """Schema for materials synthesis procedure extraction from scientific literature, based on the PcMSP dataset."""
    model_config = ConfigDict(extra='forbid')

    entities: PcMSPEntities = Field(..., description='Named entities extracted from the text.')
    relations: List[PcMSPRelation] = Field(..., description='Typed directed relations between entities.')
