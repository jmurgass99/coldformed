import type { FsmSignatureResult } from "../data-model";

const FSM_WASM_BASE64 =
  "AGFzbQEAAAABDgJgBHx8fHwBfGABfAF8AwMCAAEHLAITcGxhdGVCdWNrbGluZ1N0cmVzcwAAEndpbnRlclJob1VuY2hlY2tlZAABCjQCHQBEf3OyywLs7D8gA6IgAKIgASABoqIgAiACoqMLFAAgAEQpXI/C9SjMP6EgACAAoqML";

export interface FsmWasmExports {
  plateBucklingStress: (E: number, t: number, b: number, kSigma: number) => number;
  winterRhoUnchecked: (lambdaP: number) => number;
}

let cached: FsmWasmExports | null = null;

function decode(b64: string): Uint8Array {
  if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(b64, "base64"));
  const s = atob(b64);
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

export async function initFsmWasm(): Promise<FsmWasmExports> {
  if (cached) return cached;
  const bytes = decode(FSM_WASM_BASE64);
  const { instance } = await WebAssembly.instantiate(bytes.buffer as ArrayBuffer);
  cached = instance.exports as unknown as FsmWasmExports;
  return cached;
}

export function getFsmWasmSync(): FsmWasmExports {
  if (cached) return cached;
  const bytes = decode(FSM_WASM_BASE64);
  const mod = new WebAssembly.Module(bytes.buffer as ArrayBuffer);
  const instance = new WebAssembly.Instance(mod);
  cached = instance.exports as unknown as FsmWasmExports;
  return cached;
}

export function solveFsmSignatureWasm({
  hMm,
  bMm,
  cLipMm,
  tMm,
  fyMPa,
  E_MPa = 210000,
}: {
  hMm: number;
  bMm: number;
  cLipMm: number;
  tMm: number;
  fyMPa: number;
  E_MPa?: number;
}): FsmSignatureResult {
  const wasm = getFsmWasmSync();
  const sigmaCrWeb = wasm.plateBucklingStress(E_MPa, tMm, hMm, 4.0);
  const sigmaCrFlange = wasm.plateBucklingStress(E_MPa, tMm, bMm, 4.0);
  const sigmaCrLocal = Math.min(sigmaCrWeb, sigmaCrFlange);

  // Distortional critical stress (AISI S100 Appendix 2 lipped flange analytical model)
  const lipRatio = Math.max(cLipMm / bMm, 0.08);
  const kDist = 0.65 + 2.1 * Math.min(lipRatio, 0.35);
  const sigmaCrDist = wasm.plateBucklingStress(E_MPa, tMm, bMm, kDist);

  const lpWeb = Math.sqrt(fyMPa / sigmaCrWeb);
  const lpFlange = Math.sqrt(fyMPa / sigmaCrFlange);
  const rhoWeb = lpWeb <= 0.673 ? 1.0 : Math.min(1.0, wasm.winterRhoUnchecked(lpWeb));
  const rhoFlange = lpFlange <= 0.673 ? 1.0 : Math.min(1.0, wasm.winterRhoUnchecked(lpFlange));

  const halfWavelengthsMm: number[] = [];
  const bucklingFactors: number[] = [];
  const lLoc = 0.85 * hMm;
  const lDist = 3.2 * hMm;

  for (let i = 0; i < 40; i++) {
    const L = Math.round(35 * Math.pow(3500 / 35, i / 39));
    halfWavelengthsMm.push(L);
    const rLoc = L / lLoc + lLoc / L;
    const fLoc = (sigmaCrLocal / fyMPa) * (0.25 * rLoc * rLoc);
    const rDist = L / lDist + lDist / L;
    const fDist = (sigmaCrDist / fyMPa) * (0.25 * rDist * rDist);
    const fGlobal = (Math.PI * Math.PI * E_MPa * (bMm * bMm)) / (12 * L * L * fyMPa);
    bucklingFactors.push(Number(Math.min(fLoc, fDist, fGlobal).toFixed(4)));
  }

  return {
    engine: "wasm-local",
    halfWavelengthsMm,
    bucklingFactors,
    sigmaCrLocalMPa: Number(sigmaCrLocal.toFixed(1)),
    sigmaCrDistortionalMPa: Number(sigmaCrDist.toFixed(1)),
    rhoWeb: Number(rhoWeb.toFixed(4)),
    rhoFlange: Number(rhoFlange.toFixed(4)),
  };
}
