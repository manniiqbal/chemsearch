"use client"

import { useMemo, useState } from "react"
import { API_BASE_URL, predictReaction, simulateReaction } from "../lib/api"
import type { Participant, PredictionCandidate, PredictionResult, ReactionConditions, SimulationResult } from "../lib/types"
import { ConditionsForm, ParticipantEditor } from "./ReactionEditors"
import { PredictionResults, SimulationResults } from "./ReactionResults"
import { ReactionViewer } from "./ReactionViewer"

const defaultConditions: ReactionConditions = { temperature_c: null, pressure_bar: null, duration_minutes: null, ph: null, solvent: null, notes: null }

const examples = [
    { title: "Aerobic oxidation", equation: "ethanol + oxygen → ethanoic acid + water", reactants: ["ethanol", "oxygen"], reagents: [], catalysts: [], structures: ["CCO", "O=O"] },
    { title: "Hydrogenation", equation: "ethene + hydrogen → ethane", reactants: ["ethene"], reagents: ["hydrogen"], catalysts: ["platinum"], structures: ["C=C"] },
    { title: "Bromination", equation: "ethene + bromine → 1,2-dibromoethane", reactants: ["ethene"], reagents: ["bromine"], catalysts: [], structures: ["C=C"] },
    { title: "Esterification", equation: "ethanoic acid + methanol → methyl ethanoate", reactants: ["ethanoic acid", "methanol"], reagents: [], catalysts: ["sulfuric acid"], structures: ["CC(=O)O", "CO"] },
] as const

const toParticipants = (values: string[]): Participant[] => values.map((canonical_smiles) => ({ canonical_smiles, coefficient: 1 }))
const legacyReactionTypes = ["aerobic_oxidation", "alcohol_oxidation", "hydrogenation", "alkene_halogenation", "carbonyl_reduction", "esterification", "ester_hydrolysis", "nucleophilic_substitution"]
const cleanLabel = (value: string) => value.replaceAll("_", " ").replaceAll("-", " ")

async function resolveMolecule(value: string) {
    const query = value.trim()
    if (!query) throw new Error("Remove blank chemical fields or enter a chemical name.")
    for (const inputType of ["smiles", "name"] as const) {
        const response = await fetch(`${API_BASE_URL}/api/search/molecule-search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, input_type: inputType }),
        })
        const data = await response.json().catch(() => ({})) as { message?: string; molecule?: { canonical_smiles?: string } }
        if (response.ok && data.molecule?.canonical_smiles) return data.molecule.canonical_smiles
        if (inputType === "name") throw new Error(`“${query}” was not recognised. Check the spelling or try a SMILES formula.`)
    }
    throw new Error(`“${query}” was not recognised.`)
}

function validateConditions(conditions: ReactionConditions) {
    if (conditions.temperature_c != null && conditions.temperature_c < -273.15) return "Temperature cannot be below absolute zero."
    if (conditions.pressure_bar != null && conditions.pressure_bar <= 0) return "Pressure must be greater than 0 bar."
    if (conditions.duration_minutes != null && conditions.duration_minutes <= 0) return "Duration must be greater than 0 minutes."
    if (conditions.ph != null && (conditions.ph < 0 || conditions.ph > 14)) return "pH must be between 0 and 14."
    return null
}

export default function ChemWorkspace() {
    const [reactants, setReactants] = useState<string[]>(["ethanol", "oxygen"])
    const [reagents, setReagents] = useState<string[]>([])
    const [catalysts, setCatalysts] = useState<string[]>([])
    const [resolvedReactants, setResolvedReactants] = useState<string[]>(["CCO", "O=O"])
    const [resolvedContext, setResolvedContext] = useState<string[]>([])
    const [conditions, setConditions] = useState(defaultConditions)
    const [result, setResult] = useState<SimulationResult | null>(null)
    const [prediction, setPrediction] = useState<PredictionResult | null>(null)
    const [selectedCandidate, setSelectedCandidate] = useState<PredictionCandidate | null>(null)
    const [activeOutput, setActiveOutput] = useState<"rules" | "ml">("rules")
    const [loading, setLoading] = useState(false)
    const [mlLoading, setMlLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const reactantParticipants = useMemo(() => toParticipants(resolvedReactants), [resolvedReactants])
    const products = activeOutput === "ml"
        ? selectedCandidate?.products ?? prediction?.candidates[0]?.products ?? []
        : result?.product_sets[0]?.products ?? []

    function loadExample(index: number) {
        const example = examples[index]
        setReactants([...example.reactants]); setReagents([...example.reagents]); setCatalysts([...example.catalysts])
        setResolvedReactants([...example.structures]); setResolvedContext([]); setConditions(defaultConditions); setResult(null); setPrediction(null); setSelectedCandidate(null); setActiveOutput("rules"); setError(null)
    }

    async function run() {
        if (!reactants.length || reactants.every((value) => !value.trim())) { setError("Add at least one starting chemical."); return }
        if (reactants.length > 4) { setError("This simulator supports up to four starting chemicals at once."); return }
        const conditionError = validateConditions(conditions)
        if (conditionError) { setError(conditionError); return }

        setLoading(true); setError(null); setResult(null)
        try {
            const [canonicalReactants, canonicalReagents, canonicalCatalysts] = await Promise.all([
                Promise.all(reactants.map(resolveMolecule)),
                Promise.all(reagents.map(resolveMolecule)),
                Promise.all(catalysts.map(resolveMolecule)),
            ])
            setResolvedReactants(canonicalReactants)
            setResolvedContext([...canonicalReagents, ...canonicalCatalysts])
            const payload = {
                reactants: toParticipants(canonicalReactants),
                reagents: toParticipants([...canonicalReagents, ...canonicalCatalysts]),
                reaction_type: null,
                conditions,
            }
            let response = await simulateReaction(payload)
            if (response.warnings.some((warning) => warning.toLowerCase().includes("reaction type is required"))) {
                for (const reactionType of legacyReactionTypes) {
                    const candidate = await simulateReaction({ ...payload, reaction_type: reactionType })
                    if (candidate.status === "simulated") { response = candidate; break }
                }
            }
            setResult(response)
            setActiveOutput("rules")
            if (response.status !== "simulated") setError(cleanLabel(response.warnings[0] ?? "No supported reaction was found for those chemicals."))
        } catch (caught) {
            setError(caught instanceof Error ? caught.message : "Something went wrong. Please try again.")
        } finally { setLoading(false) }
    }

    async function runMlPrediction() {
        if (!reactants.length || reactants.every((value) => !value.trim())) { setError("Add at least one starting chemical."); return }
        setMlLoading(true); setError(null)
        try {
            const [canonicalReactants, canonicalReagents, canonicalCatalysts] = await Promise.all([
                Promise.all(reactants.map(resolveMolecule)),
                Promise.all(reagents.map(resolveMolecule)),
                Promise.all(catalysts.map(resolveMolecule)),
            ])
            setResolvedReactants(canonicalReactants)
            setResolvedContext([...canonicalReagents, ...canonicalCatalysts])
            const response = await predictReaction({
                reactants: toParticipants(canonicalReactants),
                reagents: toParticipants([...canonicalReagents, ...canonicalCatalysts]),
                conditions,
            })
            setPrediction(response)
            setSelectedCandidate(response.candidates[0] ?? null)
            setActiveOutput("ml")
            if (!response.candidates.length) setError(response.warnings[0] ?? "The ML model did not return a valid product.")
        } catch (caught) {
            setError(caught instanceof Error ? caught.message : "The ML prediction could not be completed.")
        } finally { setMlLoading(false) }
    }

    const annotation = activeOutput === "ml"
        ? cleanLabel(selectedCandidate?.model_name ?? prediction?.candidates[0]?.model_name ?? "Experimental ML prediction")
        : result?.product_sets[0]?.rule_name ?? "Reaction type detected automatically"

    return (
        <main className="workbench-shell">
            <header className="site-header">
                <a className="brand" href="#top" aria-label="ChemSearch home"><span className="brand-mark">Cs</span><span><strong>ChemSearch</strong><small>Reaction workbench</small></span></a>
                <div className="scope-badge"><span className="live-dot" /> Single step simulator</div>
            </header>

            <section className="intro" id="top">
                <span className="eyebrow">Guided chemistry workspace</span>
                <h1>Enter chemicals. We identify the reaction.</h1>
                <p>Use everyday chemical names or SMILES. ChemSearch checks the inputs, applies a tested rule, and explains the product clearly.</p>
            </section>

            <section className="example-strip" aria-labelledby="examples-title">
                <div className="section-heading"><div><span className="step-number">01</span><h2 id="examples-title">Start with a tested example</h2></div><small>Useful for checking the simulator</small></div>
                <div className="example-grid">
                    {examples.map((example, index) => <button className="example-card" type="button" onClick={() => loadExample(index)} key={example.title}><strong>{example.title}</strong><span>{example.equation}</span></button>)}
                </div>
            </section>

            <section className="workspace-card">
                <div className="section-heading workspace-heading"><div><span className="step-number">02</span><h2>Set up the reaction</h2></div><small>Names are converted to structures when you run it</small></div>
                <div className="input-grid">
                    <ParticipantEditor title="Starting chemicals" helper="Chemicals that will be transformed" values={reactants} onChange={setReactants} minimum={1} placeholder="e.g. ethanol" />
                    <ParticipantEditor title="Other chemicals" helper="Reactants such as oxygen, hydrogen or bromine" values={reagents} onChange={setReagents} placeholder="e.g. hydrogen" />
                    <ParticipantEditor title="Catalysts" helper="Optional — they affect the reaction but are not used up" values={catalysts} onChange={setCatalysts} placeholder="e.g. platinum" />
                    <ConditionsForm value={conditions} onChange={setConditions} />
                </div>
                {error && <div className="notice error" role="alert"><strong>Check your reaction</strong><span>{error}</span></div>}
                <div className="action-grid">
                    <button className="run-button" type="button" onClick={run} disabled={loading || mlLoading}>{loading ? <><span className="spinner" />Checking chemicals and reaction…</> : "Identify and simulate reaction"}</button>
                    <div className="ml-action">
                        <button className="secondary-button" type="button" onClick={runMlPrediction} disabled={loading || mlLoading}>{mlLoading ? <><span className="spinner light" />Running ReactionT5…</> : "Try experimental ML prediction"}</button>
                        <small>For broader reactions outside the tested rule library. Results may be slower or chemically inaccurate.</small>
                    </div>
                </div>
            </section>

            <section className="reaction-section" aria-labelledby="reaction-title">
                <div className="section-heading"><div><span className="step-number">03</span><h2 id="reaction-title">Reaction result</h2></div><small>Structures and detected rule</small></div>
                <ReactionViewer reactants={reactantParticipants} products={products} reagents={toParticipants(resolvedContext)} conditions={conditions} annotation={annotation} />
                {activeOutput === "ml"
                    ? <PredictionResults result={prediction} selectedRank={(selectedCandidate ?? prediction?.candidates[0])?.rank ?? 1} onSelect={(candidate) => setSelectedCandidate(candidate)} />
                    : <SimulationResults result={result} />}
            </section>

            <footer><strong>Supported scope</strong><span>Tested single step rules cover aerobic oxidation, alcohol oxidation, hydrogenation, halogenation, carbonyl reduction, esterification, ester hydrolysis and nucleophilic substitution. ReactionT5 provides separate experimental suggestions for broader inputs.</span></footer>
        </main>
    )
}
