import type { ReactionConditions } from "../lib/types"

export function ParticipantEditor({
    title,
    values,
    onChange,
    minimum = 0,
}: {
    title: string
    values: string[]
    onChange: (values: string[]) => void
    minimum?: number
}) {
    const update = (index: number, value: string) => {
        const next = [...values]
        next[index] = value
        onChange(next)
    }
    return (
        <section className="form-section">
            <div className="form-heading">
                <div><span className="eyebrow">Input</span><h3>{title}</h3></div>
                <button className="text-button" type="button" onClick={() => onChange([...values, ""])}>+ Add molecule</button>
            </div>
            {values.length === 0 && <button className="empty-input" type="button" onClick={() => onChange([""])}>Add optional {title.toLowerCase()}</button>}
            {values.map((value, index) => (
                <div className="input-row" key={index}>
                    <span className="input-index">{String(index + 1).padStart(2, "0")}</span>
                    <input value={value} onChange={(event) => update(index, event.target.value)} placeholder="Enter canonical or valid SMILES" aria-label={`${title} ${index + 1}`} />
                    <button className="remove-button" type="button" disabled={values.length <= minimum} onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))} aria-label={`Remove ${title.toLowerCase()} ${index + 1}`}>×</button>
                </div>
            ))}
        </section>
    )
}

type ConditionKey = keyof ReactionConditions

export function ConditionsForm({ value, onChange }: { value: ReactionConditions; onChange: (value: ReactionConditions) => void }) {
    const numberField = (key: ConditionKey, raw: string) => onChange({ ...value, [key]: raw === "" ? null : Number(raw) })
    return (
        <section className="form-section compact-section">
            <div className="form-heading"><div><span className="eyebrow">Optional</span><h3>Reaction conditions</h3></div></div>
            <div className="condition-grid">
                <label>Temperature <span>°C</span><input type="number" value={value.temperature_c ?? ""} onChange={(e) => numberField("temperature_c", e.target.value)} placeholder="25" /></label>
                <label>Pressure <span>bar</span><input type="number" value={value.pressure_bar ?? ""} onChange={(e) => numberField("pressure_bar", e.target.value)} placeholder="1" /></label>
                <label>Duration <span>min</span><input type="number" value={value.duration_minutes ?? ""} onChange={(e) => numberField("duration_minutes", e.target.value)} placeholder="60" /></label>
                <label>pH<input type="number" value={value.ph ?? ""} onChange={(e) => numberField("ph", e.target.value)} placeholder="7" /></label>
                <label className="wide-field">Solvent<input value={value.solvent ?? ""} onChange={(e) => onChange({ ...value, solvent: e.target.value || null })} placeholder="e.g. ethanol" /></label>
            </div>
        </section>
    )
}
