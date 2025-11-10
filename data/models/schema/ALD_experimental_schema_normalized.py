from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Unit(BaseModel):
    hasQuantityKind: Optional[str] = None
    sameAs: Optional[List[str]] = None

class QuantityValue(BaseModel):
    numericValue: Optional[float] = None
    unit: Optional[Unit] = None

class NormalizedString(BaseModel):
    value: str
    sameAs: Optional[List[str]] = None

class Method(Enum):
    PEALD = 'PEALD'
    TALD = 'TALD'
    SALD = 'SALD'

class AldMethodItem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    compound: NormalizedString = Field(..., description='Name of subcomponent, e.g., InOx, ZnO, GaOx, TiO2.')
    method: Method = Field(..., description='ALD method used for this compound.')

class AldSystem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    aldMethod: List[AldMethodItem] = Field(..., description='List of ALD techniques used for each compound deposited for this sample.')
    materialDeposited: NormalizedString = Field(..., description='The material being deposited, e.g., TiO2, Copper.')

class PrecursorItem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    compound: NormalizedString
    precursor: NormalizedString

class CoReactantItem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    compound: NormalizedString
    coReactant: NormalizedString

class ReactantSelection(BaseModel):
    precursor: Optional[List[PrecursorItem]] = Field(
        None, description='List of precursors for each compound.'
    )
    coReactant: Optional[List[CoReactantItem]] = Field(
        None, description='List of co-reactants used for each compound.'
    )
    carrierGas: Optional[NormalizedString] = Field(
        None, description='Type of carrier gas used in the delivery of reactants.'
    )
    purgingGas: Optional[NormalizedString] = Field(
        None,
        description='Inert gas used to purge residual precursors and reactants in the chamber.',
    )

class Reactor(BaseModel):
    name: str = Field(..., description='Name of the reactor.')
    manufacturer: Optional[str] = Field(None, description='Manufacturer of the reactor.')

class PlasmaPower(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Temperature(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Pressure(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Value1(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Value(BaseModel):
    model_config = ConfigDict(extra='forbid')

    compound: str
    value: Value1

class NumberofCycles(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class FilmThickness(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class GrowthPerCycle(BaseModel):
    model_config = ConfigDict(extra='forbid')

    values: List[Value]
    numberofCycles: Optional[NumberofCycles] = Field(
        None, description='Total number of ALD cycles performed.'
    )
    filmThickness: Optional[FilmThickness] = Field(
        None, description='Final film thickness in nanometers.'
    )

class NucleationPeriod(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Precursor(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class CoReactant(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class DosingTimeItem(BaseModel):
    compound: Optional[str] = None
    precursor: Optional[Precursor] = Field(
        None, description='Time for dosing the precursor, measured in seconds.'
    )
    coReactant: Optional[CoReactant] = Field(
        None, description='Time for dosing the co-reactant, measured in seconds.'
    )

class Precursor1(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class CoReactant1(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class PurgeTimeItem(BaseModel):
    compound: Optional[str] = None
    precursor: Optional[Precursor1] = Field(
        None,
        description='Time for purging the reactor chamber after precursor dosing, measured in seconds.',
    )
    coReactant: Optional[CoReactant1] = Field(
        None,
        description='Time for purging the reactor chamber after co-reactant dosing, measured in seconds.',
    )

class PrecursorFlow(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class CoReactantFlow(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class PurgingGasFlow(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class FlowRate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    compound: str
    precursorFlow: PrecursorFlow
    coReactantFlow: CoReactantFlow
    purgingGasFlow: Optional[PurgingGasFlow] = None

class ThicknessControl(BaseModel):
    growthPerCycle: Optional[GrowthPerCycle] = Field(
        None, description='Growth per cycle (GPC) for each compound.'
    )
    saturation: Optional[bool] = Field(
        None,
        description='Indicates if saturation conditions are achieved during dosing and purging.',
    )
    nucleationPeriod: Optional[NucleationPeriod] = Field(
        None,
        description='Initial growth behavior of the film during the first few ALD cycles, measured in cycles.',
    )
    dosingTime: Optional[List[DosingTimeItem]] = Field(
        None,
        description='Dosing times per compound for the precursor and the co-reactant.',
    )
    purgeTime: Optional[List[PurgeTimeItem]] = Field(
        None,
        description='Purge times per compound after the precursor and co-reactant dose.',
    )
    flowRates: Optional[List[FlowRate]] = Field(
        None, description='Flow rates of reactants per compound (in sccm).'
    )

class Count(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class NumberofSubcycle(BaseModel):
    model_config = ConfigDict(extra='forbid')

    compound: str
    count: Count

class SupercycleDesign(BaseModel):
    model_config = ConfigDict(extra='forbid')

    numberofSubcycles: Optional[List[NumberofSubcycle]] = Field(
        None, description='Number of ALD subcycles per compound within the supercycle.'
    )
    subcycleSequence: Optional[List[str]] = Field(
        None, description='Sequence of subcycles in the supercycle.'
    )

class ProcessParameters(BaseModel):
    reactor: Optional[Reactor] = Field(
        None, description='Type and details of the reactor used for the ALD process.'
    )
    plasmaPower: Optional[PlasmaPower] = Field(
        None, description='Plasma power (in Watts) if PEALD was used.'
    )
    substrate: Optional[NormalizedString] = Field(
        None,
        description='The surface where the material was deposited at (e.g., Si wafer, glass, polymer).',
    )
    deliveryMethod: Optional[str] = Field(
        None,
        description='Method of delivering the precursor and co-reactant to the reaction chamber.',
    )
    temperature: Optional[Temperature] = Field(
        None,
        description='The temperature at which deposition occurs, typically in °C.',
    )
    pressure: Optional[Pressure] = Field(
        None,
        description='The pressure within the reactor during deposition, typically in Torr.',
    )
    thicknessControl: Optional[ThicknessControl] = Field(
        None, description='Control and verification of material thickness per cycle.'
    )
    supercycleDesign: Optional[SupercycleDesign] = Field(
        None,
        description='Supercycle design used in multicomponent ALD processes. Not applicable for binary processes.Highly effects final film properties.',
    )

class RefractiveIndex(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class AbsorptionCoefficient(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class BandGap(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class OpticalProperties(BaseModel):
    refractiveIndex: Optional[RefractiveIndex] = Field(
        None, description='Refractive index of the film.'
    )
    absorptionCoefficient: Optional[AbsorptionCoefficient] = Field(
        None, description='Optical absorption coefficient.'
    )
    bandGap: Optional[BandGap] = Field(None, description='Measured optical band gap.')
    characterizationMethod: Optional[str] = Field(
        None, description='Method used to determine band gap (e.g., Tauc plot, UV-Vis).'
    )

class Resistivity(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class CarrierDensity(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Mobility(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ElectricalProperties(BaseModel):
    resistivity: Optional[Resistivity] = Field(
        None, description='Electrical resistivity of the film.'
    )
    carrierDensity: Optional[CarrierDensity] = Field(
        None, description='Carrier density in the film.'
    )
    mobility: Optional[Mobility] = Field(
        None, description='Carrier mobility in the film.'
    )
    characterizationMethod: Optional[str] = Field(
        None, description='Method used (e.g., Hall measurements).'
    )

class Variation(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Uniformity(BaseModel):
    variation: Optional[Variation] = Field(
        None,
        description='Permissible variation in film thickness, typically measured in percentage.',
    )

class AspectRatio(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Conformality(BaseModel):
    aspectRatio: Optional[AspectRatio] = Field(
        None,
        description='Aspect ratio of the 3D structures used in testing conformality.',
    )

class Values(BaseModel):
    model_config = ConfigDict(extra='forbid')

    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ElementalConcentration(BaseModel):
    values: Values
    characterizationMethod: Optional[str] = Field(
        None,
        description='Analytical technique used to determine elemental concentration (e.g., XPS, EDS, RBS).',
    )

class AtomicRatio(BaseModel):
    Elements: Optional[List[str]] = Field(
        None,
        description="Ordered list of element symbols in the ratio (e.g., ['In', 'Ga', 'Zn']).",
    )
    value: str = Field(
        ..., description="Ratio in colon-separated format (e.g., '1.1:1.5:1.3')."
    )
    characterizationMethod: Optional[str] = Field(
        None, description='Technique used to determine the ratio, if mentioned.'
    )

class FilmComposition(BaseModel):
    model_config = ConfigDict(extra='forbid')

    elementalConcentration: Optional[ElementalConcentration] = Field(
        None,
        description='Measured elemental concentrations, typically reported as atomic percent (at.%) or weight percent (wt.%) depending on the technique.',
    )
    atomicRatio: Optional[AtomicRatio] = Field(
        None,
        description='Reported atomic ratios of elements (not to be confused with concentration).',
    )

class Crystallinity(BaseModel):
    model_config = ConfigDict(extra='forbid')

    phase: Optional[str] = Field(
        None, description='Described phase, e.g., amorphous, polycrystalline.'
    )
    characterizationMethod: Optional[str] = Field(
        None, description='Method used (e.g., XRD, TEM).'
    )

class Value2(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Roughness(BaseModel):
    model_config = ConfigDict(extra='forbid')

    value: Optional[Value2] = Field(None, description='Root mean square roughness.')
    characterizationMethod: Optional[str] = Field(
        None, description='Method used (e.g., AFM).'
    )

class Value3(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class FilmDensity(BaseModel):
    model_config = ConfigDict(extra='forbid')

    value: Optional[Value3] = Field(None, description='Density of the deposited film.')
    characterizationMethod: Optional[str] = Field(
        None, description='Measurement method (e.g., XRR, ellipsometry).'
    )

class MaterialProperties(BaseModel):
    opticalProperties: Optional[OpticalProperties] = None
    electricalProperties: Optional[ElectricalProperties] = None
    uniformity: Optional[Uniformity] = Field(
        None,
        description='Assessment of film thickness uniformity across large substrate areas.',
    )
    conformality: Optional[Conformality] = Field(
        None, description='Ability of the film to coat 3D structures uniformly.'
    )
    filmComposition: Optional[FilmComposition] = Field(
        None,
        description='Elemental composition data derived from film characterization.',
    )
    chemicalComposition: Optional[str] = Field(
        None, description='Chemical composition of the deposited film.'
    )
    crystallinity: Optional[Crystallinity] = Field(
        None, description='Phase and structural state of the deposited film.'
    )
    roughness: Optional[Roughness] = Field(
        None, description='Surface roughness of the film.'
    )
    filmDensity: Optional[FilmDensity] = Field(
        None, description='Density of the film, typically measured in g/cm3.'
    )

class FieldEffectMobility(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ThresholdVoltage(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class SubthresholdSwing(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class OnOffRatio(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class DeviceProperties(BaseModel):
    model_config = ConfigDict(extra='forbid')

    fieldEffectMobility: Optional[FieldEffectMobility] = Field(
        None,
        description="Field-effect mobility (μ_FE), extracted from the device's transfer characteristics.",
    )
    thresholdVoltage: Optional[ThresholdVoltage] = Field(
        None,
        description='Threshold voltage (V_TH). Can be positive or negative depending on the device type.',
    )
    subthresholdSwing: Optional[SubthresholdSwing] = Field(
        None, description='Subthreshold swing (SS).'
    )
    onOffRatio: Optional[OnOffRatio] = Field(
        None, description='On/off drain current ratio (I_ON/I_OFF) of the TFT.'
    )
    deviceStructure: Optional[str] = Field(
        None,
        description='Description of the device stack or architecture (e.g., bottom-gate top-contact). Optional but useful for correlating performance.',
    )

class OtherAspects(BaseModel):
    safety: Optional[str] = Field(
        None,
        description='Safety considerations for handling chemicals and reaction products.',
    )
    filmStability: Optional[bool] = Field(
        None,
        description='Whether the film remains stable under intended environmental conditions.',
    )
    reproducibility: Optional[bool] = Field(
        None, description='Consistency of results in repeated experiments.'
    )

class ALDProcessNormalized(BaseModel):
    aldSystem: AldSystem = Field(..., description='Details about the ALD system used.')
    reactantSelection: ReactantSelection = Field(
        ...,
        description='Selection of precursor and co-reactant based on their reactivity, volatility, and safety.',
    )
    processParameters: ProcessParameters = Field(
        ...,
        description='Specific parameters under which the ALD process is carried out.',
    )
    materialProperties: MaterialProperties = Field(
        ..., description='Assessment of the properties of the deposited film.'
    )
    deviceProperties: DeviceProperties = Field(
        ...,
        description='Performance metrics of thin-film transistor (TFT) devices that incorporate this deposited material. These reflect device-level characteristics, not intrinsic film properties.',
    )
    otherAspects: OtherAspects = Field(
        ...,
        description='Other important aspects of the ALD process development such as safety and reproducibility.',
    )

class ALDProcessNormalizedList(BaseModel):
    processes: List[ALDProcessNormalized]