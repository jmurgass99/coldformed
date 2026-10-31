# Changelog

## 1.1.0 — 2026-10-31

Correcciones y añadidos encontrados al ejecutar los casos de uso del README.

- `distortional.aisi_distortional_buckling`: reimplementado con AISI S100-16 Apéndice 2 (§2.3.1.3 compresión, §2.3.3.3 flexión con ξ_web = 2, propiedades del conjunto ala-labio de la Tabla 2.3.1.3-1). La versión anterior mezclaba (π/L)² con (π/L)⁴ en k_φfe y omitía k̃_φwg, de modo que σ_crd salía del orden de 10⁶ MPa y P_nd = P_y siempre. Para una C 200x60x20x2 (S350) ahora σ_crd = 228 MPa con L_cr = 588 mm en compresión y 556 MPa con 531 mm en flexión; anclado por sustitución a mano y comprobaciones de consistencia (`tests/test_aisi_distortional_appendix2.py`). Nuevos parámetros opcionales `L_m_mm` (distancia entre arriostramientos) y `k_phi_restraint_N` (rigidez rotacional de la chapa). El resultado añade `sigma_crd_flex_MPa` y `L_crd_flex_mm`; `Mcrd_kNm` usa la tensión de flexión.
- `fsm_assembly.refine_profile_strips`: subdivide cada franja en n subfranjas. Con una franja por elemento el mínimo local de una C 200x60x20x2 salía en 154 MPa; con cuatro subfranjas baja a 109 MPa (alma aislada: 76 MPa).
- Limitación documentada: la curva de firma del ensamblado de franjas finitas reproduce el modo local pero no el distorsional ni el global.
- 30 casos de uso ejecutados en `examples/` con su salida en `examples/output/`; README reescrito; metadatos del paquete alineados.

## 1.0.0

Publicación inicial como repositorio independiente (origen: ColdFormedJm del monorepo Structural JM).
