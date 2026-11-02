import assert from "node:assert/strict";
import { getStripMesh } from "../mesh/getMesh.ts";
import { initFsmWasm, solveFsmSignatureWasm } from "../solver/wasmSolver.ts";

// 1. Strip geometry mapping
const m = getStripMesh(200, 75, 20, 2.0, 4);
assert.equal(m.strips.length, 20);
assert.equal(m.nodesYZ.length, 21);
assert.equal(m.geometryMapping.wallToStrips.get("web")?.length, 4);

// 2. FSM signature curve in WASM
await initFsmWasm();
const res = solveFsmSignatureWasm({
  hMm: 200,
  bMm: 75,
  cLipMm: 20,
  tMm: 2.0,
  fyMPa: 355,
});

assert.ok(res.sigmaCrLocalMPa > 50);
assert.ok(res.rhoWeb < 1.0);
assert.equal(res.bucklingFactors.length, 40);

console.log(
  `ColdFormed WASM test OK: sigma_cr_local=${res.sigmaCrLocalMPa.toFixed(1)} MPa, rho_web=${res.rhoWeb.toFixed(3)}`
);
