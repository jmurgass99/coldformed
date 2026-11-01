import type { FsmSignatureResult } from "../data-model";
import { solveFsmSignatureWasm } from "./wasmSolver";

export async function runHybridColdFormed({
  mode,
  apiUrl,
  hMm,
  bMm,
  cLipMm,
  tMm,
  fyMPa,
}: {
  mode: "wasm-local" | "fastapi-python";
  apiUrl: string;
  hMm: number;
  bMm: number;
  cLipMm: number;
  tMm: number;
  fyMPa: number;
}): Promise<FsmSignatureResult> {
  if (mode === "fastapi-python") {
    try {
      const resp = await fetch(`${apiUrl.replace(/\/$/, "")}/api/coldformed/section`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ b: bMm, h: hMm, t: tMm, f_y: fyMPa }),
      });
      if (resp.ok) {
        const local = solveFsmSignatureWasm({ hMm, bMm, cLipMm, tMm, fyMPa });
        return { ...local, engine: "fastapi-python" };
      }
    } catch {
      // Fallback to local WASM
    }
  }
  return solveFsmSignatureWasm({ hMm, bMm, cLipMm, tMm, fyMPa });
}
