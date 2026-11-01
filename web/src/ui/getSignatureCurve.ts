import van, { type State } from "vanjs-core";

export function getSignatureCurve({
  halfWavelengthsMm,
  bucklingFactors,
  rhoWeb,
  rhoFlange,
}: {
  halfWavelengthsMm: State<number[]>;
  bucklingFactors: State<number[]>;
  rhoWeb: State<number>;
  rhoFlange: State<number>;
}): HTMLElement {
  const wrap = document.createElement("div");
  wrap.style.display = "flex";
  wrap.style.flexDirection = "column";
  wrap.style.gap = "12px";

  const cSig = document.createElement("canvas");
  cSig.className = "cf-chart";
  const cRho = document.createElement("canvas");
  cRho.className = "cf-chart";

  const makeCard = (t: string, c: HTMLCanvasElement) => {
    const d = document.createElement("div");
    d.className = "cf-card";
    const h = document.createElement("h3");
    h.textContent = t;
    d.append(h, c);
    return d;
  };

  wrap.append(
    makeCard("Curva de Firma FSM σcr(L) / fy vs Semionda L [mm]", cSig),
    makeCard("Factores de Ancho Eficaz de Winter ρ (EN 1993-1-5)", cRho),
  );

  van.derive(() => {
    const Ls = halfWavelengthsMm.val;
    const fs = bucklingFactors.val;
    const ctx1 = cSig.getContext("2d");
    if (ctx1 && Ls.length > 1) {
      const w = (cSig.width = cSig.clientWidth || 320);
      const h = (cSig.height = cSig.clientHeight || 175);
      ctx1.clearRect(0, 0, w, h);

      const minLog = Math.log10(Ls[0] || 35);
      const maxLog = Math.log10(Ls[Ls.length - 1] || 3500);
      const maxF = Math.min(Math.max(...fs, 1.5), 4.0);

      ctx1.strokeStyle = "#38bdf8";
      ctx1.lineWidth = 2;
      ctx1.beginPath();
      Ls.forEach((L, i) => {
        const px = 30 + ((Math.log10(L) - minLog) / (maxLog - minLog)) * (w - 42);
        const py = h - 24 - (Math.min(fs[i], maxF) / maxF) * (h - 38);
        if (i === 0) ctx1.moveTo(px, py);
        else ctx1.lineTo(px, py);
      });
      ctx1.stroke();
    }

    const ctx2 = cRho.getContext("2d");
    if (ctx2) {
      const w = (cRho.width = cRho.clientWidth || 320);
      const h = (cRho.height = cRho.clientHeight || 175);
      ctx2.clearRect(0, 0, w, h);
      const items: [string, number, string][] = [
        ["Alma (ρ_web)", rhoWeb.val, "#38bdf8"],
        ["Ala (ρ_flange)", rhoFlange.val, "#10b981"],
      ];
      items.forEach(([lbl, val, col], idx) => {
        const y = 35 + idx * 55;
        ctx2.fillStyle = "#f8fafc";
        ctx2.font = "12px Inter, sans-serif";
        ctx2.fillText(`${lbl}: ${(val * 100).toFixed(1)}%`, 16, y);
        ctx2.fillStyle = "rgba(148,163,184,0.2)";
        ctx2.fillRect(16, y + 8, w - 32, 16);
        ctx2.fillStyle = col;
        ctx2.fillRect(16, y + 8, (w - 32) * val, 16);
      });
    }
  });

  return wrap;
}
