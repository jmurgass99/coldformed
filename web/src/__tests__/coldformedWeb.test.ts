import { describe, expect, it } from "vitest";
import { getStripMesh } from "../mesh/getMesh";
import { initFsmWasm, solveFsmSignatureWasm } from "../solver/wasmSolver";

describe("ColdFormed Web — StripGeometryMapping + fsmKernel.wasm", () => {
  it("subdivides lipped C-section walls preserving cornerToNodes and wallToStrips", () => {
    const m = getStripMesh(200, 75, 20, 2.0, 4);
    expect(m.strips.length).toBe(20);
    expect(m.nodesYZ.length).toBe(21);
    expect(m.geometryMapping.wallToStrips.get("web")?.length).toBe(4);
  });

  it("computes plate buckling stress and Winter effective width factor in WebAssembly", async () => {
    await initFsmWasm();
    const res = solveFsmSignatureWasm({
      hMm: 200,
      bMm: 75,
      cLipMm: 20,
      tMm: 2.0,
      fyMPa: 355,
    });
    expect(res.sigmaCrLocalMPa).toBeGreaterThan(50);
    expect(res.rhoWeb).toBeLessThan(1.0);
    expect(res.bucklingFactors.length).toBe(40);
  });
});
