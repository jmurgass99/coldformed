import van from "vanjs-core";
import type { StripMesh } from "./data-model";
import { getStripMesh } from "./mesh/getMesh";
import { runHybridColdFormed } from "./solver/apiClient";
import { initFsmWasm } from "./solver/wasmSolver";
import { getSignatureCurve } from "./ui/getSignatureCurve";
import { getViewer3D } from "./viewer/getViewer3D";

const { div, h2, h3, input, label, option, select, span } = van.tags;

await initFsmWasm();

const hMm = van.state(200);
const bMm = van.state(75);
const cLipMm = van.state(20);
const tMm = van.state(2.0);
const fyMPa = van.state(355);
const divisionsPerWall = van.state(4);
const bucklingMode = van.state<"local" | "distortional">("local");
const modeAmplitude = van.state(12);
const solverMode = van.state<"wasm-local" | "fastapi-python">("wasm-local");

const mesh = van.state<StripMesh>(
  getStripMesh(hMm.val, bMm.val, cLipMm.val, tMm.val, divisionsPerWall.val),
);
const halfWavelengthsMm = van.state<number[]>([]);
const bucklingFactors = van.state<number[]>([]);
const sigmaCrLocalMPa = van.state(0);
const sigmaCrDistMPa = van.state(0);
const rhoWeb = van.state(1);
const rhoFlange = van.state(1);

van.derive(() => {
  mesh.val = getStripMesh(
    hMm.val,
    bMm.val,
    cLipMm.val,
    tMm.val,
    divisionsPerWall.val,
  );
});

van.derive(() => {
  runHybridColdFormed({
    mode: solverMode.val,
    apiUrl: "http://127.0.0.1:8000",
    hMm: hMm.val,
    bMm: bMm.val,
    cLipMm: cLipMm.val,
    tMm: tMm.val,
    fyMPa: fyMPa.val,
  }).then((res) => {
    halfWavelengthsMm.val = res.halfWavelengthsMm;
    bucklingFactors.val = res.bucklingFactors;
    sigmaCrLocalMPa.val = res.sigmaCrLocalMPa;
    sigmaCrDistMPa.val = res.sigmaCrDistortionalMPa;
    rhoWeb.val = res.rhoWeb;
    rhoFlange.val = res.rhoFlange;
  });
});

const left = div(
  { class: "cf-panel" },
  h2({ style: "font-size: 1.05rem;" }, "ColdFormed 3D — Franjas Finitas FSM"),
  div(
    { class: "cf-card" },
    h3("Malla de Franjas (wallToStrips / cornerToNodes)"),
    div(
      { class: "cf-row" },
      label("Altura alma h [mm]:"),
      input({
        type: "number",
        value: () => String(hMm.val),
        oninput: (e: Event) => (hMm.val = Math.max(60, Number((e.target as HTMLInputElement).value) || 200)),
      }),
    ),
    div(
      { class: "cf-row" },
      label("Ancho ala b [mm]:"),
      input({
        type: "number",
        value: () => String(bMm.val),
        oninput: (e: Event) => (bMm.val = Math.max(30, Number((e.target as HTMLInputElement).value) || 75)),
      }),
    ),
    div(
      { class: "cf-row" },
      label("Espesor t [mm]:"),
      input({
        type: "number",
        step: "0.2",
        value: () => String(tMm.val),
        oninput: (e: Event) => (tMm.val = Math.max(0.6, Number((e.target as HTMLInputElement).value) || 2.0)),
      }),
    ),
    div(
      { class: "cf-row" },
      label("Franjas / pared:"),
      input({
        type: "number",
        min: "1",
        max: "12",
        value: () => String(divisionsPerWall.val),
        oninput: (e: Event) =>
          (divisionsPerWall.val = Math.max(1, Number((e.target as HTMLInputElement).value) || 4)),
      }),
    ),
    div(
      { class: "cf-row" },
      label("Nudos / Franjas FSM:"),
      span(() => `${mesh.val.nodesYZ.length} / ${mesh.val.strips.length}`),
    ),
  ),
  div(
    { class: "cf-card" },
    h3("Modo de Pandeo y Motor WASM"),
    div(
      { class: "cf-row" },
      label("Modo 3D:"),
      select(
        {
          onchange: (e: Event) =>
            (bucklingMode.val = (e.target as HTMLSelectElement).value as "local" | "distortional"),
        },
        option({ value: "local" }, "Pandeo Local (Alma/Ala)"),
        option({ value: "distortional" }, "Pandeo Distorsional (Labio)"),
      ),
    ),
    div(
      { class: "cf-row" },
      label("σcr,loc / σcr,dist:"),
      span(() => `${sigmaCrLocalMPa.val} / ${sigmaCrDistMPa.val} MPa`),
    ),
  ),
);

const right = div(
  { class: "cf-panel right" },
  getSignatureCurve({
    halfWavelengthsMm,
    bucklingFactors,
    rhoWeb,
    rhoFlange,
  }),
);

document.body.appendChild(
  div(
    { class: "cf-layout" },
    left,
    getViewer3D({
      mesh,
      bucklingMode,
      modeAmplitude,
    }),
    right,
  ),
);
