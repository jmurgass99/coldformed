import type { StripMesh } from "../data-model.ts";

export function getStripMesh(
  hMm: number,
  bMm: number,
  cLipMm: number,
  tMm: number,
  divisionsPerWall: number,
): StripMesh {
  const nDiv = Math.max(1, Math.floor(divisionsPerWall));
  const halfH = 0.5 * hMm;
  const corners: [string, [number, number]][] = [
    ["bot_lip_tip", [bMm, -halfH + cLipMm]],
    ["bot_flange_lip", [bMm, -halfH]],
    ["bot_web_flange", [0, -halfH]],
    ["top_web_flange", [0, halfH]],
    ["top_flange_lip", [bMm, halfH]],
    ["top_lip_tip", [bMm, halfH - cLipMm]],
  ];
  const wallNames = [
    "bottom_lip",
    "bottom_flange",
    "web",
    "top_flange",
    "top_lip",
  ];

  const cornerToNodes = new Map<string, number>();
  const wallToStrips = new Map<string, number[]>();
  const nodesYZ: [number, number][] = [];
  const strips: [number, number, number][] = [];

  cornerToNodes.set(corners[0][0], 0);
  nodesYZ.push(corners[0][1]);

  for (let w = 0; w < wallNames.length; w++) {
    const [, cStart] = corners[w];
    const [endName, cEnd] = corners[w + 1];
    const sIds: number[] = [];
    for (let k = 1; k <= nDiv; k++) {
      const a = k / nDiv;
      const pt: [number, number] = [
        cStart[0] + a * (cEnd[0] - cStart[0]),
        cStart[1] + a * (cEnd[1] - cStart[1]),
      ];
      const nPrev = nodesYZ.length - 1;
      nodesYZ.push(pt);
      const nCurr = nodesYZ.length - 1;
      sIds.push(strips.length);
      strips.push([nPrev, nCurr, tMm]);
    }
    cornerToNodes.set(endName, nodesYZ.length - 1);
    wallToStrips.set(wallNames[w], sIds);
  }

  return {
    nodesYZ,
    strips,
    geometryMapping: { cornerToNodes, wallToStrips },
  };
}
