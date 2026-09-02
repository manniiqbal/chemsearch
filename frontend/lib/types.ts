export type Mode = "simulate" | "predict" | "visualize"

export interface Participant {
    canonical_smiles: string
    coefficient: number
}

export interface ReactionConditions {
    temperature_c: number | null
    pressure_bar: number | null
    duration_minutes: number | null
    ph: number | null
    solvent: string | null
    notes?: string | null
}

export interface BondChange {
    atom1_idx: number
    atom2_idx: number
    old_bond_order: number | null
    new_bond_order: number | null
}

export interface ReactionMapping {
    atom_mappings: Array<{ reactant_atom_idx: number; product_atom_idx: number }>
    broken_bonds: BondChange[]
    formed_bonds: BondChange[]
    changed_bonds: BondChange[]
}

export interface ProductSet {
    products: Participant[]
    rule_id: string | null
    rule_name: string | null
}

export interface SimulationResult {
    status: "simulated" | "no_reaction" | "failed" | "unsupported"
    reaction_type: string | null
    product_sets: ProductSet[]
    warnings: string[]
    mappings: ReactionMapping[]
}

export interface PredictionCandidate {
    products: Participant[]
    confidence: number
    rank: number
    model_name: string | null
}

export interface PredictionResult {
    candidates: PredictionCandidate[]
    warnings: string[]
}

export interface SimulationPayload {
    reactants: Participant[]
    reagents: Participant[]
    reaction_type: string | null
    conditions: ReactionConditions
}

export type PredictionPayload = Omit<SimulationPayload, "reaction_type">

export interface ApiErrorBody {
    category?: string
    message?: string
    detail?: unknown
}
