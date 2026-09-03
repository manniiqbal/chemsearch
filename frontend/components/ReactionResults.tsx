import type { PredictionCandidate, PredictionResult, SimulationResult } from "../lib/types"
import { MoleculeViewer } from "./MoleculeViewer"

const cleanLabel = (value: string) => value.replaceAll("_", " ").replaceAll("-", " ")

function EmptyResult({ mode }: { mode: "simulate" | "predict" }) {
    return <div className="results-empty" data-result-mode={mode}><span>⌁</span><strong>No result yet</strong><p>Choose an example or enter chemicals, then run the simulator.</p></div>
}

export function SimulationResults({ result }: { result: SimulationResult | null }) {
    if (!result) return <EmptyResult mode="simulate" />
    return <>
        <div className="status-row"><span className={`status-pill ${result.status}`}>{result.status === "simulated" ? "Reaction found" : cleanLabel(result.status)}</span><small>{result.reaction_type ? cleanLabel(result.reaction_type) : null}</small></div>
        {result.product_sets.map((set, index) => (
            <article className="result-card" key={`${set.rule_id}-${index}`}>
                <div className="result-title"><span>{index === 0 ? "Main product" : `Alternative ${index + 1}`}</span><small>{set.rule_name}</small></div>
                {set.products.map((product, productIndex) => <MoleculeViewer key={productIndex} smiles={product.canonical_smiles} />)}
                {result.mappings[index] && <BondSummary mapping={result.mappings[index]} />}
            </article>
        ))}
        {result.warnings.map((warning, index) => <div className="notice warning" key={index}>{warning}</div>)}
    </>
}

function BondSummary({ mapping }: { mapping: SimulationResult["mappings"][number] }) {
    const changes = mapping.broken_bonds.length + mapping.formed_bonds.length + mapping.changed_bonds.length
    return <div className="bond-summary"><span>{mapping.atom_mappings.length} atoms mapped</span><span>{changes} bond {changes === 1 ? "change" : "changes"}</span></div>
}

export function PredictionResults({ result, selectedRank, onSelect }: { result: PredictionResult | null; selectedRank: number; onSelect: (candidate: PredictionCandidate) => void }) {
    if (!result) return <EmptyResult mode="predict" />
    if (!result.candidates.length) return <div className="notice">The model returned no valid product structures.</div>
    return <>
        <div className="score-note">Scores are relative beam weights, not calibrated probabilities.</div>
        {result.candidates.map((candidate) => (
            <button className={`candidate-card ${candidate.rank === selectedRank ? "selected" : ""}`} key={candidate.rank} onClick={() => onSelect(candidate)}>
                <div className="candidate-heading"><span className="rank">#{candidate.rank}</span><strong>{(candidate.confidence * 100).toFixed(1)}%</strong></div>
                {candidate.products.map((product, index) => <MoleculeViewer key={index} smiles={product.canonical_smiles} />)}
                <small>{candidate.model_name ? cleanLabel(candidate.model_name) : null}</small>
            </button>
        ))}
        {result.warnings.map((warning, index) => <div className="notice warning" key={index}>{warning}</div>)}
    </>
}
