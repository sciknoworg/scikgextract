from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PolyIEEntities(BaseModel):
    """Named entities extracted from polymer scientific text."""
    model_config = ConfigDict(extra='forbid')

    chemicalNames: List[str] = Field(
        ..., description='Chemical/polymer names or abbreviations (e.g., P3HT, PEDOT:PSS, poly(3-hexylthiophene)).'
    )
    propertyNames: List[str] = Field(
        ..., description='Names of measured properties (e.g., PCE, Voc, Jsc, decomposition temperature, band gap).'
    )
    propertyValues: List[str] = Field(
        ..., description='Measured values with units (e.g., 3.8%, 0.9 V, 437 °C).'
    )
    conditions: Optional[List[str]] = Field(
        None, description='Experimental conditions under which measurements were taken (e.g., 5% weight loss, room temperature).'
    )


class PolyIERelation(BaseModel):
    """A relation linking a chemical name to a property name and its value, optionally with a condition."""
    model_config = ConfigDict(extra='forbid')

    chemicalName: str = Field(..., description='The chemical/polymer name this property belongs to.')
    propertyName: str = Field(..., description='The name of the measured property.')
    propertyValue: Optional[str] = Field(None, description='The measured value with unit.')
    condition: Optional[str] = Field(None, description='The experimental condition, if applicable.')


class PolyIESchema(BaseModel):
    """Schema for polymer property extraction from scientific literature, based on the PolyIE dataset."""
    model_config = ConfigDict(extra='forbid')

    entities: PolyIEEntities = Field(..., description='Named entities extracted from the text.')
    relations: List[PolyIERelation] = Field(
        ..., description='Relations linking a chemical name to a property name and its value, optionally with a condition.'
    )
