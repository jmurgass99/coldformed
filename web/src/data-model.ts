export interface StripGeometryMapping {
  cornerToNodes: Map<string, number>;
  wallToStrips: Map<string, number[]>;
}

export interface StripMesh {
  nodesYZ: [number, number][];
  strips: [number, number, number][];
  geometryMapping: StripGeometryMapping;
}

export interface FsmSignatureResult {
  engine: "wasm-local" | "fastapi-python";
  halfWavelengthsMm: number[];
  bucklingFactors: number[];
  sigmaCrLocalMPa: number;
  sigmaCrDistortionalMPa: number;
  rhoWeb: number;
  rhoFlange: number;
}
