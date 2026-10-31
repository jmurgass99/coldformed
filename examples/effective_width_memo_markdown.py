"""Memoria de cálculo del ancho eficaz de una placa comprimida (Bryan → λ_p → ρ → b_eff).

Alma de 180 mm y 1,5 mm bajo una tensión actuante de 250 MPa, placa apoyada en ambos
bordes (k = 4). `render_effective_width_memo` escribe los cuatro pasos en Markdown y
LaTeX listos para un informe. Esta memoria usa la esbeltez con la tensión actuante,
λ_p = √(σ/σ_cr), y la expresión ρ = (λ_p − 0,22)/λ_p² de compresión uniforme (AISI /
EN 1993-1-5 con ψ = 1).

Ejecutar:  python examples/effective_width_memo_markdown.py
"""
from coldformed.memos.aisi_effective_width import EffectiveWidthMemoInput, render_effective_width_memo


def main() -> None:
    memo = render_effective_width_memo(EffectiveWidthMemoInput(b_mm=180.0, t_mm=1.5, sigma_act_MPa=250.0))
    print(f"σ_cr = {memo.sigma_cr_MPa:.1f} MPa, λ_p = {memo.lambda_p:.3f}, ρ = {memo.rho:.3f}, "
          f"b_eff = {memo.b_eff_mm:.1f} mm\n")
    print(memo.markdown)
    print("LaTeX:")
    print(memo.latex)


if __name__ == "__main__":
    main()
