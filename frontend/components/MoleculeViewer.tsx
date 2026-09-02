"use client"

import { useEffect, useState } from "react"
import { renderMolecule } from "../lib/api"

const svgCache = new Map<string, string>()

export function MoleculeViewer({ smiles, label }: { smiles: string; label?: string }) {
    const [rendered, setRendered] = useState(() => ({
        smiles,
        svg: svgCache.get(smiles) ?? "",
        failed: false,
    }))
    const cached = svgCache.get(smiles)
    const svg = cached ?? (rendered.smiles === smiles ? rendered.svg : "")
    const failed = rendered.smiles === smiles && rendered.failed

    useEffect(() => {
        let active = true
        if (svgCache.has(smiles)) return () => { active = false }
        renderMolecule(smiles)
            .then((result) => {
                svgCache.set(smiles, result.svg)
                if (active) setRendered({ smiles, svg: result.svg, failed: false })
            })
            .catch(() => { if (active) setRendered({ smiles, svg: "", failed: true }) })
        return () => { active = false }
    }, [smiles])

    return (
        <article className="molecule-card">
            {label && <span className="molecule-label">{label}</span>}
            <div className={`molecule-art ${!svg ? "loading" : ""}`}>
                {svg ? (
                    <div dangerouslySetInnerHTML={{ __html: svg }} />
                ) : failed ? (
                    <span className="molecule-fallback">Unable to depict molecule</span>
                ) : (
                    <span className="structure-loader" aria-label="Rendering structure" />
                )}
            </div>
            <code title={smiles}>{smiles}</code>
        </article>
    )
}
