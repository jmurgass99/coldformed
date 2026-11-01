import * as THREE from "three";
import van, { type State } from "vanjs-core";
import type { StripMesh } from "../data-model";

export function getViewer3D({
  mesh,
  bucklingMode,
  modeAmplitude,
}: {
  mesh: State<StripMesh>;
  bucklingMode: State<"local" | "distortional">;
  modeAmplitude: State<number>;
}): HTMLElement {
  const container = document.createElement("div");
  container.className = "cf-viewer";

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 1, 5000);
  camera.position.set(340, -450, 260);
  camera.up.set(0, 0, 1);
  camera.lookAt(40, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  container.appendChild(renderer.domElement);

  const group = new THREE.Group();
  scene.add(group);

  van.derive(() => {
    while (group.children.length > 0) group.remove(group.children[0]);
    const m = mesh.val;
    const mode = bucklingMode.val;
    const amp = modeAmplitude.val;
    const lengthExtrude = 400;
    const nLong = 14;

    const wallColors: Record<string, number> = {
      bottom_lip: 0xf43f5e,
      bottom_flange: 0xf59e0b,
      web: 0x38bdf8,
      top_flange: 0xf59e0b,
      top_lip: 0xf43f5e,
    };

    for (const [wallName, stripIds] of m.geometryMapping.wallToStrips.entries()) {
      const col = wallColors[wallName] ?? 0x38bdf8;
      const pts: THREE.Vector3[] = [];

      for (const sIdx of stripIds) {
        const [na, nb] = m.strips[sIdx];
        const [ya, za] = m.nodesYZ[na];
        const [yb, zb] = m.nodesYZ[nb];

        for (let k = 0; k < nLong; k++) {
          const x1 = -0.5 * lengthExtrude + (k / nLong) * lengthExtrude;
          const x2 = -0.5 * lengthExtrude + ((k + 1) / nLong) * lengthExtrude;
          const wave1 = Math.sin((Math.PI * (k / nLong)) * (mode === "local" ? 3 : 1));
          const wave2 = Math.sin((Math.PI * ((k + 1) / nLong)) * (mode === "local" ? 3 : 1));

          const d1 = wallName === "web" && mode === "local" ? amp * wave1 : 0;
          const d2 = wallName === "web" && mode === "local" ? amp * wave2 : 0;
          const f1 = wallName.includes("lip") && mode === "distortional" ? amp * wave1 : 0;
          const f2 = wallName.includes("lip") && mode === "distortional" ? amp * wave2 : 0;

          pts.push(
            new THREE.Vector3(ya + d1, x1, za + f1),
            new THREE.Vector3(yb + d1, x1, zb + f1),
            new THREE.Vector3(ya + d1, x1, za + f1),
            new THREE.Vector3(ya + d2, x2, za + f2),
          );
        }
      }

      group.add(
        new THREE.LineSegments(
          new THREE.BufferGeometry().setFromPoints(pts),
          new THREE.LineBasicMaterial({ color: col }),
        ),
      );
    }

    renderer.render(scene, camera);
  });

  const ro = new ResizeObserver(() => {
    const w = container.clientWidth || 700;
    const h = container.clientHeight || 500;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    renderer.render(scene, camera);
  });
  ro.observe(container);

  return container;
}
