import type { Participant, ReactionConditions } from "../lib/types"
import { MoleculeViewer } from "./MoleculeViewer"

function conditionSummary(conditions: ReactionConditions) {
    return [
        conditions.temperature_c != null ? `${conditions.temperature_c} °C` : null,
        conditions.pressure_bar != null ? `${conditions.pressure_bar} bar` : null,
        conditions.duration_minutes != null ? `${conditions.duration_minutes} min` : null,
        conditions.ph != null ? `pH ${conditions.ph}` : null,
        conditions.solvent,
    ].filter(Boolean).join(" · ")
}

export function ReactionViewer({
    reactants,
    products,
    reagents,
    conditions,
    annotation,
}: {
    reactants: Participant[]
    products: Participant[]
    reagents: Participant[]
    conditions: ReactionConditions
    annotation?: string
}) {
    const context = [
        reagents.length ? reagents.map((item) => item.canonical_smiles).join(" + ") : null,
        conditionSummary(conditions) || null,
    ].filter(Boolean)

    if (!reactants.length) {
        return <div className="stage-empty"><span className="orbital-mark">⌬</span><strong>Build a reaction</strong><p>Enter SMILES below to render true 2D structures.</p></div>
    }

    return (
        <div className="reaction-flow">
            <section className="reaction-side">
                <span className="eyebrow">Reactants</span>
                <div className="molecule-list">
                    {reactants.map((item, index) => <MoleculeViewer key={`${item.canonical_smiles}-${index}`} smiles={item.canonical_smiles} />)}
                </div>
            </section>
            <div className="arrow-column">
                {context.length > 0 && <span className="arrow-context">{context.join(" / ")}</span>}
                <div className="reaction-arrow"><span /></div>
                <span className="arrow-caption">{annotation ?? "Awaiting result"}</span>
            </div>
            <section className="reaction-side">
                <span className="eyebrow">Products</span>
                {products.length ? (
                    <div className="molecule-list">
                        {products.map((item, index) => <MoleculeViewer key={`${item.canonical_smiles}-${index}`} smiles={item.canonical_smiles} />)}
                    </div>
                ) : <div className="product-awaiting">Run the workflow to populate products</div>}
            </section>
        </div>
    )
}
