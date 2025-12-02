from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

class Unit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    hasQuantityKind: Optional[str] = None
    sameAs: Optional[str] = None

class QuantityValue(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    numericValue: Optional[float] = None
    unit: Optional[Unit] = None

class Method(Enum):
    DFT = 'DFT'
    HF = 'HF'
    post_HF = 'post-HF'
    ML = 'ML'
    kMC = 'kMC'
    MD = 'MD'
    Hybrid_ONIOM = 'Hybrid ONIOM'
    CCSD_T_ = 'CCSD(T)'
    MP2 = 'MP2'
    Continuum_Fluid_Dynamics__CFD_ = 'Continuum Fluid Dynamics (CFD)'
    RMD = 'RMD'
    Monte_Carlo = 'Monte Carlo'
    Lattice_Boltzmann_Method__LBM_ = 'Lattice Boltzmann Method (LBM)'
    Group_Contribution_Method__GCM_ = 'Group Contribution Method (GCM)'
    Computer_Aided_Molecular_Design__CAMD_ = 'Computer-Aided Molecular Design (CAMD)'

class Timestep(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class MethodDetails(BaseModel):
    model_config = ConfigDict(extra='forbid')

    timestep: Optional[Timestep] = Field(
        None, description='Timestep used in MD simulations.'
    )
    functional: Optional[str] = Field(
        None, description='Functional used in DFT calculations, e.g., B3LYP.'
    )
    basisSet: Optional[str] = Field(
        None,
        description='Basis set used in quantum chemical calculations, e.g., 6-31G(d,p).',
    )
    clusterModel: Optional[str] = Field(
        None, description='Cluster model used (e.g., Si9H12, Si23H24)'
    )

class Source(BaseModel):
    model_config = ConfigDict(extra='forbid')

    method: Optional[str] = Field(
        None,
        description='Method used to obtain the data (e.g., simulation, experiment)',
    )

class SimulationParameters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    methods: Optional[List[Method]] = Field(
        None, description='Computational methods used in the ALD process simulation.'
    )
    methodDetails: Optional[MethodDetails] = Field(
        None, description='Details specific to the computational methods used.'
    )
    source: Optional[Source] = None

class LigandModification(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    originalLigand: Optional[str] = Field(
        None, description='Original ligand before modification.'
    )
    modifiedLigand: Optional[str] = Field(
        None, description='Ligand after modification.'
    )

class Materials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    precursors: Optional[List[str]] = Field(
        None, description='List of precursors used in the ALD process.'
    )
    coReactants: Optional[List[str]] = Field(
        None, description='List of co-reactants used in the ALD process.'
    )
    substrates: Optional[List[str]] = Field(
        None, description='List of substrates used in the ALD process.'
    )
    encapsulationMaterials: Optional[List[str]] = Field(
        None, description='Materials used for encapsulation in selective growth.'
    )
    ligandModification: Optional[LigandModification] = Field(
        None,
        description='Details of any modifications to ligands, such as conversion from methoxy to hydroxyl.',
    )

class Rate(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class TemperatureDependence(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class GrowthRate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    rate: Optional[Rate] = Field(None, description='Growth rate of the film per cycle.')
    temperatureDependence: Optional[TemperatureDependence] = Field(
        None, description='Temperature dependence of the growth rate.'
    )
    propertySource: Optional[str] = Field(
        None, description='Source of the property (e.g., calculated, observed)'
    )

class DesorptionRate(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class DiffusionRate(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ReactionRate(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class StickingCoefficient(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class BindingAffinity(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Coverage(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class SurfaceCoverage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    coverage: Optional[Coverage] = Field(
        None, description='Percentage of surface coverage.'
    )
    timeDependent: Optional[bool] = Field(
        None, description='Indicates if surface coverage is time-dependent.'
    )

class ChemisorbedPrecursorDensity(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class SurfaceHydroxylConcentration(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ChemisorptionCharacteristics(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    chemisorbedPrecursorDensity: Optional[ChemisorbedPrecursorDensity] = Field(
        None, description='Density of chemisorbed precursor.'
    )
    stericHindrance: Optional[str] = Field(
        None, description='Description of steric hindrance effects.'
    )
    surfaceHydroxylConcentration: Optional[SurfaceHydroxylConcentration] = Field(
        None, description='Concentration of surface hydroxyl groups.'
    )

class ActivationEnergy(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class AdsorptionEnergy(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ReactionPathway(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    precursor: Optional[str] = Field(
        None, description='Precursor involved in the reaction.'
    )
    coReactant: Optional[str] = Field(
        None, description='Co-reactant involved in the reaction.'
    )
    intermediateComplex: Optional[str] = Field(
        None, description='Description of the intermediate complex formed.'
    )
    activationEnergy: Optional[ActivationEnergy] = Field(
        None, description='Activation energy for the reaction.'
    )
    adsorptionEnergy: Optional[AdsorptionEnergy] = Field(
        None, description='Adsorption energy of the precursor or co-reactant.'
    )

class SurfaceProperties(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    desorptionRate: Optional[DesorptionRate] = Field(
        None, description='Rate of surface desorption.'
    )
    diffusionRate: Optional[DiffusionRate] = Field(
        None, description='Rate of surface diffusion.'
    )
    reactionRate: Optional[ReactionRate] = Field(
        None, description='Rate of surface reactions.'
    )
    stickingCoefficient: Optional[StickingCoefficient] = Field(
        None, description='Probability of an adsorbate sticking to the surface.'
    )
    bindingAffinity: Optional[BindingAffinity] = Field(
        None, description='Binding affinity of the adsorbate to the surface.'
    )
    surfaceCoverage: Optional[SurfaceCoverage] = Field(
        None, description='Coverage of the surface by the adsorbate.'
    )
    chemisorptionCharacteristics: Optional[ChemisorptionCharacteristics] = Field(
        None,
        description='Details about chemisorption, steric hindrance, and ligand effects.',
    )
    reactionPathways: Optional[List[ReactionPathway]] = Field(
        None, description='Reaction pathways for specific surface reactions.'
    )
    surfaceTerminationChemistry: Optional[str] = Field(
        None,
        description='Description of the surface termination chemistry affecting precursor adsorption.',
    )
    propertySource: Optional[str] = Field(
        None, description='Source of the property (e.g., calculated, observed)'
    )

class Uniformity(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Roughness(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class Density(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class TemperatureProfileItem(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class FilmProperties(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    uniformity: Optional[Uniformity] = Field(
        None, description='Uniformity of the film.'
    )
    roughness: Optional[Roughness] = Field(
        None, description='Surface roughness of the film.'
    )
    density: Optional[Density] = Field(None, description='Density of the film.')
    temperatureProfile: Optional[List[TemperatureProfileItem]] = Field(
        None, description='Temperature profile across the film.'
    )
    chemicalComposition: Optional[List[str]] = Field(
        None, description='Elemental composition of the film.'
    )
    propertySource: Optional[str] = Field(
        None, description='Source of the property (e.g., calculated, observed)'
    )

class Pressure(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class CarrierGasFlow(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class FlowRate(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class PulseDuration(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class PurgeDuration(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class PrecursorFlow(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    flowRate: Optional[FlowRate] = Field(
        None, description='Flow rate of the precursor gas.'
    )
    pulseDuration: Optional[PulseDuration] = Field(
        None, description='Duration of precursor pulsing.'
    )
    purgeDuration: Optional[PurgeDuration] = Field(
        None, description='Duration of purging after precursor pulsing.'
    )

class GapDistance(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class ReactorConditions(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    pressure: Optional[Pressure] = Field(
        None, description='Pressure inside the reactor.'
    )
    carrierGasFlow: Optional[CarrierGasFlow] = Field(
        None, description='Flow rate of the carrier gas.'
    )
    carrierGasType: Optional[str] = Field(
        None, description='Type of carrier gas used in the reactor.'
    )
    precursorFlow: Optional[PrecursorFlow] = Field(
        None, description='Flow rate and timing of the precursor gas.'
    )
    gapDistance: Optional[GapDistance] = Field(
        None, description='Gap distance in the reactor.'
    )
    propertySource: Optional[str] = Field(
        None, description='Source of the property (e.g., calculated, observed)'
    )

class BlockingMechanisms(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    stericBlocking: Optional[str] = Field(
        None,
        description='Description of steric blocking effects, including adsorption prevention and reactivity reduction.',
    )
    chemicalPassivation: Optional[str] = Field(
        None, description='Description of chemical passivation effects on the surface.'
    )

class SelectiveGrowthMechanism(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    facetPreference: Optional[str] = Field(
        None, description='Preferred facet for selective growth, e.g., Pt(111).'
    )
    substituentEffects: Optional[str] = Field(
        None, description='Effects of substituents on precursor selectivity.'
    )
    blockingMechanisms: Optional[BlockingMechanisms] = Field(
        None, description='Mechanisms by which inhibitors block non-growth surfaces.'
    )

class NucleationDelay(BaseModel):
    quantityValue: Optional[QuantityValue] = None
    quantityKind: Optional[str] = None

class NucleationProcess(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    nucleationDelay: Optional[NucleationDelay] = Field(
        None, description='Delay in nucleation during the initial ALD cycles.'
    )
    selfCleaningEffect: Optional[bool] = Field(
        None,
        description='Indicates if a self-cleaning effect is observed during the ALD process.',
    )

class AtomicLayerDepositionAldProcessSchema(BaseModel):
    simulationParameters: SimulationParameters = Field(
        ..., description='Parameters and methodologies used in the ALD simulation.'
    )
    materials: Materials = Field(
        ..., description='Materials involved in the ALD process.'
    )
    growthRate: Optional[GrowthRate] = Field(
        None, description='Information related to the growth rate of the film.'
    )
    surfaceProperties: Optional[SurfaceProperties] = Field(
        None, description='Properties related to surface reactions and coverage.'
    )
    filmProperties: Optional[FilmProperties] = Field(
        None, description='Properties of the deposited film.'
    )
    reactorConditions: Optional[ReactorConditions] = Field(
        None, description='Conditions inside the reactor during ALD.'
    )
    selectiveGrowthMechanism: Optional[SelectiveGrowthMechanism] = Field(
        None, description='Mechanism of selective growth in ALD.'
    )
    nucleationProcess: Optional[NucleationProcess] = Field(
        None, description='Details about the nucleation process during ALD.'
    )

class ALDSimulationProcessList(BaseModel):
    processes: List[AtomicLayerDepositionAldProcessSchema]