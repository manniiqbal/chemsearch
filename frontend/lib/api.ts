import type {
    ApiErrorBody,
    PredictionPayload,
    PredictionResult,
    SimulationPayload,
    SimulationResult,
} from "./types"

export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    (process.env.NODE_ENV === "production"
        ? "https://chemsearch.onrender.com"
        : "http://127.0.0.1:8000")

export class ApiError extends Error {
    constructor(message: string, public readonly status?: number) {
        super(message)
        this.name = "ApiError"
    }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
        response = await fetch(`${API_BASE_URL}${path}`, init)
    } catch {
        throw new ApiError(
            "The chemistry service is waking up. Wait about 30 seconds and try again.",
        )
    }

    const data = (await response.json().catch(() => ({}))) as T & ApiErrorBody
    if (!response.ok) {
        throw new ApiError(
            data.message ?? `Request failed with status ${response.status}.`,
            response.status,
        )
    }
    return data
}

const jsonHeaders = { "Content-Type": "application/json" }

export function simulateReaction(payload: SimulationPayload) {
    return request<SimulationResult>("/api/reactions/simulate", {
        method: "POST",
        headers: jsonHeaders,
        body: JSON.stringify(payload),
    })
}

export function predictReaction(payload: PredictionPayload) {
    return request<PredictionResult>("/api/reactions/predict", {
        method: "POST",
        headers: jsonHeaders,
        body: JSON.stringify(payload),
    })
}

export function renderMolecule(smiles: string, width = 420, height = 280) {
    return request<{ canonical_smiles: string; svg: string }>(
        "/api/molecules/render",
        {
            method: "POST",
            headers: jsonHeaders,
            body: JSON.stringify({ smiles, width, height }),
        },
    )
}
