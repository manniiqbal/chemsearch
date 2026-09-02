"use client"

import { useMemo, useState } from "react"
import { API_BASE_URL, predictReaction, simulateReaction } from "../lib/api"
import type { Mode, Participant, PredictionCandidate, PredictionResult, ReactionConditions, SimulationResult } from "../lib/types"
import { ConditionsForm, ParticipantEditor } from "./ReactionEditors"
import { PredictionResults, SimulationResults } from "./ReactionResults"
import { ReactionViewer } from "./ReactionViewer"
import { WorkspaceSidebar } from "./WorkspaceSidebar"

const defaultConditions: ReactionConditions = { temperature_c: null, pressure_bar: null, duration_minutes: null, ph: null, solvent: null, notes: null }
const reactionPresets = [
    { value: "hydrogenation", label: "Alkene hydrogenation", description: "Ethene to ethane", reactants: ["C=C"], reagents: [] },
    { value: "alkene_halogenation", label: "Alkene halogenation", description: "Add bromine across an alkene", reactants: ["C=C"], reagents: ["BrBr"] },
    { value: "alcohol_oxidation", label: "Alcohol oxidation", description: "Ethanol to ethanal", reactants: ["CCO"], reagents: [] },
    { value: "carbonyl_reduction", label: "Carbonyl reduction", description: "Ethanal to ethanol", reactants: ["CC=O"], reagents: [] },
    { value: "esterification", label: "Esterification", description: "Ethanoic acid and methanol to an ester", reactants: ["CC(=O)O", "CO"], reagents: [] },
    { value: "ester_hydrolysis", label: "Ester hydrolysis", description: "Methyl ethanoate to acid and alcohol", reactants: ["CC(=O)OC"], reagents: [] },
    { value: "nucleophilic_substitution", label: "Nucleophilic substitution", description: "Bromoethane to ethanol", reactants: ["CCBr"], reagents: [] },
] as const

const participants = (values: string[]): Participant[] => values.filter((value) => value.trim()).map((value) => ({ canonical_smiles: value.trim(), coefficient: 1 }))

async function resolveMolecule(value: string) {
    const query = value.trim()
    for (const inputType of ["smiles", "name"] as const) {
        const response = await fetch(`${API_BASE_URL}/api/search/molecule-search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, input_type: inputType }),
        })
        const data = await response.json().catch(() => ({})) as { message?: string; molecule?: { canonical_smiles?: string } }
        if (response.ok && data.molecule?.canonical_smiles) return data.molecule.canonical_smiles
        if (inputType === "name") throw new Error(data.message ?? `Could not find “${query}”. Try a chemical name or valid SMILES.`)
    }
    throw new Error(`Could not find “${query}”.`)
}

const resolveMolecules = (values: string[]) => Promise.all(values.filter((value) => value.trim()).map(resolveMolecule))

export default function ChemWorkspace() {
    const [mode, setMode] = useState<Mode>("simulate")
    const [reactants, setReactants] = useState(["C=C"])
    const [reagents, setReagents] = useState<string[]>([])
    const [reactionType, setReactionType] = useState("hydrogenation")
    const [conditions, setConditions] = useState(defaultConditions)
    const [simulation, setSimulation] = useState<SimulationResult | null>(null)
    const [prediction, setPrediction] = useState<PredictionResult | null>(null)
    const [selectedCandidate, setSelectedCandidate] = useState<PredictionCandidate | null>(null)
    const [latestMode, setLatestMode] = useState<"simulate" | "predict" | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const reactantParticipants = useMemo(() => participants(reactants), [reactants])
    const reagentParticipants = useMemo(() => participants(reagents), [reagents])
    const simulationProducts = simulation?.product_sets[0]?.products ?? []
    const predictionProducts = selectedCandidate?.products ?? prediction?.candidates[0]?.products ?? []
    const visibleResultMode = mode === "visualize" ? latestMode : mode
    const canvasProducts = visibleResultMode === "simulate" ? simulationProducts : visibleResultMode === "predict" ? predictionProducts : []
    const annotation = visibleResultMode === "simulate"
        ? simulation?.product_sets[0]?.rule_name ?? reactionType.replaceAll("_", " ")
        : visibleResultMode === "predict" && (selectedCandidate ?? prediction?.candidates[0])
            ? `ReactionT5 · ${((selectedCandidate ?? prediction!.candidates[0]).confidence * 100).toFixed(1)}% relative score`
            : undefined
    const selectedPreset = reactionPresets.find((preset) => preset.value === reactionType) ?? reactionPresets[0]

    function loadReactionPreset(value: string) {
        const preset = reactionPresets.find((item) => item.value === value)
        if (!preset) return
        setReactionType(preset.value)
        setReactants([...preset.reactants])
        setReagents([...preset.reagents])
        setSimulation(null)
        setError(null)
    }

    async function run() {
        if (!reactantParticipants.length) { setError("Add at least one chemical name or valid SMILES."); return }
        setLoading(true); setError(null)
        try {
            const [resolvedReactants, resolvedReagents] = await Promise.all([resolveMolecules(reactants), resolveMolecules(reagents)])
            const resolvedReactantParticipants = participants(resolvedReactants)
            const resolvedReagentParticipants = participants(resolvedReagents)
            setReactants(resolvedReactants)
            setReagents(resolvedReagents)
            if (mode === "simulate") {
                const result = await simulateReaction({ reactants: resolvedReactantParticipants, reagents: resolvedReagentParticipants, reaction_type: reactionType, conditions })
                setSimulation(result); setLatestMode("simulate")
            } else if (mode === "predict") {
                const result = await predictReaction({ reactants: resolvedReactantParticipants, reagents: resolvedReagentParticipants, conditions })
                setPrediction(result); setSelectedCandidate(result.candidates[0] ?? null); setLatestMode("predict")
            }
        } catch (caught) {
            setError(caught instanceof Error ? caught.message : "An unexpected error occurred.")
        } finally { setLoading(false) }
    }

    const selectCandidate = (candidate: PredictionCandidate) => { setSelectedCandidate(candidate); setLatestMode("predict") }
    const title = mode === "simulate" ? "Rule-based simulator" : mode === "predict" ? "ML reaction predictor" : "Reaction visualizer"
    const subtitle = mode === "simulate" ? "Choose a tested example or enter common chemical names / SMILES." : mode === "predict" ? "Enter common chemical names or SMILES for ReactionT5v2." : "Inspect the latest result as structures, not raw JSON."

    return <main className="app-shell">
        <WorkspaceSidebar mode={mode} onChange={setMode} />
        <section className="workspace-main">
            <header className="topbar"><div><span className="eyebrow">Chemical intelligence / Workbench</span><h1>{title}</h1><p>{subtitle}</p></div><div className="api-state"><span className="live-dot" /> API-connected</div></header>
            <div className="canvas-panel">
                <div className="panel-heading"><div><span className="eyebrow">Live reaction canvas</span><h2>Structure overview</h2></div><span className="mode-chip">{mode}</span></div>
                <ReactionViewer reactants={reactantParticipants} products={canvasProducts} reagents={reagentParticipants} conditions={conditions} annotation={annotation} />
            </div>
            {mode !== "visualize" ? <div className="editor-panel">
                <ParticipantEditor title="Reactants" values={reactants} onChange={setReactants} minimum={1} />
                <ParticipantEditor title="Reagents" values={reagents} onChange={setReagents} />
                {mode === "simulate" && <section className="form-section compact-section"><div className="form-heading"><div><span className="eyebrow">Rule library</span><h3>Reaction class</h3></div></div><select value={reactionType} onChange={(e) => loadReactionPreset(e.target.value)}>{reactionPresets.map((preset) => <option value={preset.value} key={preset.value}>{preset.label}</option>)}</select><div className="notice"><strong>{selectedPreset.description}</strong><br /><span>Compatible example loaded automatically. You can also type chemical names or SMILES above.</span></div></section>}
                <ConditionsForm value={conditions} onChange={setConditions} />
                {error && <div className="notice error" role="alert">{error}</div>}
                <button className="run-button" onClick={run} disabled={loading}>{loading ? <><span className="spinner" />{mode === "predict" ? "ReactionT5 is reasoning…" : "Applying reaction rules…"}</> : mode === "predict" ? "Generate predictions" : "Simulate reaction"}</button>
            </div> : <div className="visualize-note">The canvas reflects your most recent workflow and selected prediction candidate.</div>}
        </section>
        <aside className="results-panel"><div className="results-header"><span className="eyebrow">Output</span><h2>Results</h2><p>{mode === "predict" ? "Select a candidate to update the canvas." : "Products, provenance and structural changes."}</p></div><div className="results-list">{mode === "predict" ? <PredictionResults result={prediction} selectedRank={(selectedCandidate ?? prediction?.candidates[0])?.rank ?? 1} onSelect={selectCandidate} /> : mode === "simulate" ? <SimulationResults result={simulation} /> : latestMode === "predict" ? <PredictionResults result={prediction} selectedRank={(selectedCandidate ?? prediction?.candidates[0])?.rank ?? 1} onSelect={selectCandidate} /> : <SimulationResults result={simulation} />}</div></aside>
    </main>
}
