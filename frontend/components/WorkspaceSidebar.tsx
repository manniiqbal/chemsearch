import type { Mode } from "../lib/types"

const modes: Array<{ id: Mode; index: string; label: string; detail: string }> = [
    { id: "simulate", index: "01", label: "Simulate", detail: "Curated reaction rules" },
    { id: "predict", index: "02", label: "Predict", detail: "ReactionT5 candidates" },
    { id: "visualize", index: "03", label: "Visualize", detail: "Latest selected result" },
]

export function WorkspaceSidebar({ mode, onChange }: { mode: Mode; onChange: (mode: Mode) => void }) {
    return (
        <aside className="sidebar">
            <div className="brand">
                <span className="brand-mark">Cs</span>
                <div><strong>ChemSearch</strong><small>Reaction workspace</small></div>
            </div>
            <nav aria-label="Workspace modes">
                <span className="nav-label">Workbench</span>
                {modes.map((item) => (
                    <button
                        key={item.id}
                        className={`mode-button ${mode === item.id ? "active" : ""}`}
                        onClick={() => onChange(item.id)}
                        aria-current={mode === item.id ? "page" : undefined}
                    >
                        <span className="mode-index">{item.index}</span>
                        <span><strong>{item.label}</strong><small>{item.detail}</small></span>
                    </button>
                ))}
            </nav>
            <div className="sidebar-note">
                <span className="live-dot" /> Linux-ready chemistry runtime
                <p>Deterministic rules and ML predictions remain clearly separated.</p>
            </div>
        </aside>
    )
}
