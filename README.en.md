# coldformed — cold-formed steel and Class 4 sections (EN 1993-1-3/1-5, AISI S100)

[Español](README.md) · **English** · [Português](README.pt.md) · [Italiano](README.it.md)

Winter effective width and classification of Class 4 sections (EN 1993-1-5 §4.4), the Direct Strength Method in bending and compression (AISI S100 / AS/NZS 4600), distortional buckling of C and Z sections by AISI S100 Appendix 2 and by EN 1993-1-3 §5.5.3 (edge stiffener), critical local plate buckling stress (Bryan and finite strips with Numba), and the checks that go with a purlin or a stud: web shear, web crippling at supports, interaction, torsion, perforations and galvanizing. The functions are pure and anchored to worked examples solved by hand.

[![CI](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What problem it solves

You have a purlin, a stud or a thin-plate girder and need to know how much of the section really works (effective width), which buckling mode governs (local, distortional or global) and what nominal and design resistance remains under the project's code. The package solves that part with the code formulas; you bring the internal forces from your model.

**Use it when**

- you classify a web or a compressed flange and need ρ, λ_p and b_eff to EN 1993-1-5 §4.4, for any ψ;
- you have the elastic critical loads or moments (from CUFSM, from the package's finite-strip curve or from Appendix 2) and want the resistance by the Direct Strength Method;
- you design C or Z purlins and need distortional buckling by AISI and by Eurocode, with their applicability limits;
- you want the critical stress of an isolated plate (four boundary conditions) or to check the finite-strip assembly against the closed-form solution;
- you check web shear (AISI §G2), web crippling at supports (§G5), interaction (§H1), Saint-Venant torsion or the reduction for holes.

**Don't use it for**

- obtaining internal forces: there is no frame or load analysis;
- web shear to EN 1993-1-3 §6.1.5: only AISI §G2 is available;
- distortional and global modes from the finite-strip curve: the current assembly reproduces the local mode and shows neither the distortional minimum nor the global flattening (see limitations); for σ_crd use Appendix 2 and for the global mode, Euler or your own program;
- Σ, omega or hat sections in the distortional modules: they cover C and Z with a simple lip;
- lateral-torsional buckling of the purlin (M_cre): it is passed as input.

## Installation

```bash
pip install git+https://github.com/jmurgass99/coldformed.git
pip install "coldformed[api,ml] @ git+https://github.com/jmurgass99/coldformed.git"   # REST API and scikit-learn surrogate
```

Dependencies: `numpy`, `scipy`, `numba` and `sectionproperties`. For development: `git clone`, `pip install -e ".[test,api,ml]"`, `pytest -q` (27 test files). On Windows, if the console is not UTF-8, run the examples with `python -X utf8 examples/<name>.py`.

## Capabilities

| Capability | Modules | Code or reference | Use cases |
|---|---|---|---|
| Effective width and Class 4: λ_p, Winter's ρ with ψ, classification and approximate W_eff, iteration of effective properties, calculation report | `class4_evaluator`, `services.section_service`, `effective_iter`, `memos.aisi_effective_width` | EN 1993-1-5 §4.4 (eq. 4.2, 4.3, Table 4.1), EN 1993-1-3 §5.5.2 | [6 cases](#1-effective-width-and-class-4-sections-en-1993-1-5) |
| Direct Strength Method in bending and compression, φ/γ factors and dispatch by code (US, CO, AU, EU, SG) | `direct_strength`, `codes_multi` | AISI S100-16/22 §E2–E4, §F2–F4; AS/NZS 4600; NSR-10 F.4; EN 1993-1-3 | [5 cases](#2-direct-strength-method-and-multi-code-dispatch) |
| Distortional buckling of C and Z: σ_crd and L_cr by Appendix 2 (compression and bending), edge stiffener with spring K and χ_d, applicability limits | `distortional` | AISI S100-16 Appendix 2 §2.3.1.3 and §2.3.3.3, Table B4.1-1; EN 1993-1-3 §5.5.3, Table 5.1 | [5 cases](#3-distortional-buckling-of-c-and-z-sections) |
| Local plate buckling: Bryan with four boundary conditions, finite strips with a Numba kernel and signature curve, surrogate model | `fsm`, `local_buckling`, `fsm_jit`, `fsm_assembly`, `signature_curve`, `surrogates` | Timoshenko & Gere §9.3; Schafer 2008 (CUFSM); Cheung 1976 | [5 cases](#4-local-plate-buckling-and-finite-strips) |
| Complementary checks: web shear, web crippling at supports, M-V and P-M interaction, torsion of open sections, holes, galvanizing | `shear`, `web_crippling`, `interaction`, `torsion_open`, `perforations`, `galvanizing` | AISI S100-16 §G2, §G5, §H1, §1.1.2; EN 1993-1-3 §10; EN ISO 1461 | [5 cases](#5-complementary-checks-aisi-s100) |
| Section catalogue, properties with `sectionproperties`, cost and CO₂, polygon for SAP2000 and REST API | `profile_catalog`, `sectprops_wrapper`, `cost_estimator`, `sap_section_bridge`, `api` | — | [4 cases](#6-catalogue-section-properties-cost-export-and-api) |

The 30 scripts in `examples/` were run in a clean environment before publishing; their output is in `examples/output/` and is what is reproduced here.

## Use cases

The outputs are reproduced exactly as the scripts print them, in Spanish.

### 1. Effective width and Class 4 sections (EN 1993-1-5)

#### Class 4 plate girder: how much web and how much flange actually work

Winter's ρ for the web in pure bending (ψ = −1, k_σ = 23.9) and for the compressed flange (ψ = +1, k_σ = 4) at several slendernesses, and the master's course reference case (record W00777): web 1 488×10 in S355 → ρ = 0.69.

<details><summary>Actual output of <code>python examples/plate_girder_class4_web_flange_effective_width_en1993_1_5.py</code></summary>

```text
Acero S355, ε = 0.814

Alma en flexión pura  (ψ = -1, k_σ = 23.9)
     b/t     λ_p      ρ  b_eff/b
      80   0.708  1.000   100.0%
     100   0.885  0.989    98.9%
     124   1.098  0.820    82.0%
     150   1.328  0.691    69.1%
     200   1.770  0.530    53.0%
     250   2.213  0.429    42.9%

Ala comprimida apoyada en ambos bordes  (ψ = +1, k_σ = 4.0)
     b/t     λ_p      ρ  b_eff/b
      30   0.649  1.000   100.0%
      38   0.822  0.891    89.1%
      42   0.909  0.834    83.4%
      50   1.082  0.736    73.6%
      60   1.298  0.640    64.0%
      80   1.731  0.504    50.4%

Alma 1500 x 10 mm en flexión: λ_p = 1.328, ρ = 0.69 → altura eficaz comprimida = 518 mm de 750 mm
```

</details>

#### Web of a C 200.74.2 purlin under a stress gradient (ψ = −0.74)

Exercise 16 of the UPC master's course (record W01486): k_σ by the Table 4.1 formula and ρ = 0.85. With the wrong ψ or with the outstand formula the record's result is not obtained.

<details><summary>Actual output of <code>python examples/exam_c200_purlin_web_stress_gradient_psi_w01486.py</code></summary>

```text
C 200.74.2, S350GD: h_p = 198.0 mm, t = 1.96 mm, ψ = -0.74
  ε = 0.8194, k_σ = 17.82 (fórmula Tabla 4.1)
  λ_p = 1.0283   (ficha: 1,03)
  ρ   = 0.8549   (ficha: 0,85)
  altura eficaz comprimida de la parte plana: ρ·h_p = 169.3 mm de 198 mm

Mismo λ_p con hipótesis equivocadas:
  ψ = +1 (compresión uniforme): ρ = 0.764
  fórmula de voladizo (0,188):  ρ = 0.795
  Ninguna reproduce el 0,85 de la ficha: el término 0,055·(3+ψ) y el umbral dependen de ψ.
```

</details>

#### Two more webs from the master's course: CF 200.2 in S460 and Z 350.3 in S350GD

Records W01527 and W01482, with a different yield strength and b/t ratio from the reference case. The Z one is a plate-level statement (the record does not deduct corners).

<details><summary>Actual output of <code>python examples/exam_cf200_s460_and_z350_webs_pure_bending_w01527_w01482.py</code></summary>

```text
caso                                      b/t      ε    λ_p      ρ | ficha λ_p / ρ
CF 200.2, S460 (W01527)                  99.0  0.715  0.998  0.892 | 1.00 / 0.890
Z 350.3, S350GD (W01482)                116.7  0.819  1.025  0.871 | 1.03 / 0.867
Viga armada 1488x10, S355 (W00777)      148.8  0.814  1.317  0.696 | 1.32 / 0.690

Las fichas redondean λ_p a dos decimales antes de evaluar ρ; la diferencia con el valor exacto es de 0,001 a 0,003 en ρ.
```

</details>

#### Welded box: class and approximate effective modulus for several thicknesses

`Class4Section` idealises the box by b, h and a single thickness; `evaluate_section` wraps it with validation.

<details><summary>Actual output of <code>python examples/box_section_class_check_and_effective_modulus.py</code></summary>

```text
Cajón b = 400 mm, h = 1000 mm, S355 (ε = 0.814, límites Clase 3: alma 100.9, ala 34.2)

 t [mm]     h/t    b/t  clase  W_eff [cm³]
    6.0   166.7   66.7      4        777.1
    8.0   125.0   50.0      4       2207.5
   10.0   100.0   40.0      4       4823.0
   12.0    83.3   33.3      3       6545.1
   15.0    66.7   26.7      3       8103.5
   20.0    50.0   20.0      3      10633.4

Servicio evaluate_section (t = 8 mm): {'section_class': 4, 'epsilon': 0.813617, 'w_eff_cm3': 2207.49}
Entrada inválida (t = 0): GeometryError: t debe ser > 0 (recibido 0.0)
```

</details>

#### Effective width calculation report in Markdown and LaTeX

The four steps (σ_cr, λ_p with the acting stress, ρ, b_eff) ready for a report.

<details><summary>Actual output of <code>python examples/effective_width_memo_markdown.py</code></summary>

```text
σ_cr = 52.7 MPa, λ_p = 2.178, ρ = 0.413, b_eff = 74.3 mm

# Memoria — Ancho efectivo (EN 1993-1-5 / AISI)

**Geometría:** b = 180.0 mm, t = 1.50 mm, b/t = 120.0
**Esfuerzo actuante:** σ = 250.0 MPa

## Paso 1 — Esfuerzo crítico de placa (Bryan)

σ_cr = k · π² · E / [12 · (1-ν²) · (b/t)²]
σ_cr = 4.0 · π² · 210000 / [12 · (1 - 0.3²) · 120.0²]
**σ_cr = 52.7 MPa**

## Paso 2 — Esbeltez de placa

λ_p = √(σ/σ_cr) = √(250.0/52.7) = 2.178

## Paso 3 — Factor de reducción

λ_p = 2.178 > 0.673 → ρ = (λ_p - 0.22)/λ_p² = (2.178 - 0.22)/2.178² = **0.413**

## Paso 4 — Ancho efectivo

**b_eff = ρ · b = 0.413 · 180.0 = 74.3 mm**

LaTeX:
\sigma_{cr} = \frac{k\pi^2 E}{12(1-\nu^2)(b/t)^2} = 52.7\;\text{MPa}\\\lambda_p = \sqrt{\sigma/\sigma_{cr}} = 2.178\\\rho = 0.413\\b_{eff} = \rho\,b = 74.3\;\text{mm}
```

</details>

#### Iteration of effective properties with the global model

The model solves with the gross section; each effective-width reduction raises the stress and forces another reduction. The loop converges in a few iterations.

<details><summary>Actual output of <code>python examples/effective_properties_iteration_with_fem_demand.py</code></summary>

```text
tol = 0.05   iteraciones =  5  convergió = True  b_eff/b final = 0.214
         historia del ratio: 1.000, 0.427, 0.291, 0.243, 0.223, 0.214
tol = 0.01   iteraciones =  7  convergió = True  b_eff/b final = 0.208
         historia del ratio: 1.000, 0.427, 0.291, 0.243, 0.223, 0.214, 0.210, 0.208
tol = 0.001  iteraciones = 10  convergió = True  b_eff/b final = 0.207
         historia del ratio: 1.000, 0.427, 0.291, 0.243, 0.223, 0.214, 0.210, 0.208, 0.207, 0.207, 0.207

Con la sección bruta el alma parecía eficaz al 100 %; converge a un ratio bastante menor porque cada reducción eleva la tensión y vuelve a reducir.
```

</details>

### 2. Direct Strength Method and multi-code dispatch

#### Bending: which mode governs as M_crl and M_crd vary

With M_y fixed, a sweep of the local and distortional critical moments to see which mode limits and how much it costs.

<details><summary>Actual output of <code>python examples/dsm_flexure_mode_sweep_aisi_s100.py</code></summary>

```text
M_y = S_f·f_y = 11.90 kN·m, M_cre = 30.0 kN·m

  M_crl   M_crd |    M_nl    M_nd    M_ne |     M_n  gobierna
------------------------------------------------------------------
    6.0     8.0 |    7.96    8.00   11.77 |    7.96  local
    6.0    10.5 |    7.96    8.87   11.77 |    7.96  local
    6.0    16.0 |    7.96   10.28   11.77 |    7.96  local
    9.0     8.0 |    9.15    8.00   11.77 |    8.00  distortional
    9.0    10.5 |    9.15    8.87   11.77 |    8.87  distortional
    9.0    16.0 |    9.15   10.28   11.77 |    9.15  local
   14.0     8.0 |   10.58    8.00   11.77 |    8.00  distortional
   14.0    10.5 |   10.58    8.87   11.77 |    8.87  distortional
   14.0    16.0 |   10.58   10.28   11.77 |   10.28  distortional
   25.0     8.0 |   11.77    8.00   11.77 |    8.00  distortional
   25.0    10.5 |   11.77    8.87   11.77 |    8.87  distortional
   25.0    16.0 |   11.77   10.28   11.77 |   10.28  distortional

M_n = min(M_nl, M_nd, M_ne); la columna 'gobierna' indica el modo que limita.
```

</details>

#### C stud in compression: effect of the unbraced length

P_crl of the web, P_crd from Appendix 2 and Euler's P_cre for each length; the DSM returns the governing mode.

<details><summary>Actual output of <code>python examples/dsm_compression_stud_column_unbraced_length_sweep.py</code></summary>

```text
A = 420 mm², P_y = 147.0 kN
σ_crl (alma, k = 4) = 75.9 MPa → P_crl = 31.9 kN
σ_crd (Schafer)     = 224.0 MPa → P_crd = 94.1 kN, L_crd = 470 mm

 L [m]   P_cre    P_ne    P_nl    P_nd     P_n  gobierna
   1.0   248.7   114.8    62.6    91.0    62.6  local
   1.5   110.5    84.3    51.3    91.0    51.3  local
   2.0    62.2    54.5    38.7    91.0    38.7  local
   2.5    39.8    34.9    28.8    91.0    28.8  local
   3.0    27.6    24.2    22.5    91.0    22.5  local
   4.0    15.5    13.6    13.6    91.0    13.6  local

φ_c = 0,85 (LRFD) se aplica después con codes_multi.design_resistance_compression.
```

</details>

#### C stud: local from the FSM curve, distortional from Appendix 2, global from Euler

Each critical load by the route the package solves well, and then `dsm_compression`.

<details><summary>Actual output of <code>python examples/stud_dsm_local_from_fsm_distortional_from_appendix2.py</code></summary>

```text
C 200x60x20x2.0, A = 720 mm², L = 2400 mm
  local (FSM refinado):       σ_crl =  108.6 MPa a λ = 148 mm → P_crl = 78.2 kN
  distorsional (Apéndice 2):  σ_crd =  227.9 MPa a L_cr = 588 mm → P_crd = 164.1 kN
  global (Euler, I_min dato): P_cre = 107.9 kN

DSM: P_y = 252.0  P_ne = 94.7  P_nl = 75.5  P_nd = 157.2  →  P_n = 75.5 kN, gobierna local; φ_c·P_n = 64.2 kN
```

</details>

#### Design capacity by code: AISI (US, CO, AU) against EN 1993-1-3 (EU, SG)

`design_capacity_cz` applies DSM or the effective width method depending on the code; they are not the same method and the numbers show it.

<details><summary>Actual output of <code>python examples/multicode_design_capacity_c_section_us_co_au_eu.py</code></summary>

```text
C 200x65x20x2.0, f_y = 350 MPa

US: AISI S100-22 Specification for Cold-Formed Steel (DSM)
   compression  nominal =   160.70 kN   diseño =   136.59 kN   método: Direct Strength Method (DSM)
   bending      nominal =    14.16 kN·m diseño =    12.74 kN·m método: Direct Strength Method (DSM)
CO: NSR-10 §F.4 (basado en AISI DSM)
   compression  nominal =   160.70 kN   diseño =   136.59 kN   método: Direct Strength Method (DSM)
   bending      nominal =    14.16 kN·m diseño =    12.74 kN·m método: Direct Strength Method (DSM)
AU: AS/NZS 4600:2018 Cold-formed steel structures (DSM)
   compression  nominal =   160.70 kN   diseño =   136.59 kN   método: Direct Strength Method (DSM)
   bending      nominal =    14.16 kN·m diseño =    12.74 kN·m método: Direct Strength Method (DSM)
EU: EN 1993-1-3:2006 Eurocode 3 Part 1-3 (EWM)
   compression  nominal =   164.91 kN   diseño =   164.91 kN   método: Effective Width Method (EWM §5.5.3 Edge Stiffener)
   bending      nominal =    16.04 kN·m diseño =    16.04 kN·m método: Effective Width Method (EWM §5.5.3 Edge Stiffener)
SG: SS EN 1993-1-3 (NA Singapore EWM)
   compression  nominal =   164.91 kN   diseño =   164.91 kN   método: Effective Width Method (EWM §5.5.3 Edge Stiffener)
   bending      nominal =    16.04 kN·m diseño =    16.04 kN·m método: Effective Width Method (EWM §5.5.3 Edge Stiffener)
```

</details>

#### Resistance factors by code

AISI and AS/NZS φ against Eurocode γ_M on the same nominal resistance.

<details><summary>Actual output of <code>python examples/resistance_factors_by_code_dsm_vs_ewm.py</code></summary>

```text
M_n = 18.2 kN·m, P_n = 95.0 kN

código  M_d [kN·m]  P_d [kN]  norma
US           16.38     80.75  AISI S100-22 Specification for Cold-Formed Steel (DSM)
CO           16.38     80.75  NSR-10 §F.4 (basado en AISI DSM)
AU           16.38     80.75  AS/NZS 4600:2018 Cold-formed steel structures (DSM)
EU           18.20     95.00  EN 1993-1-3:2006 Eurocode 3 Part 1-3 (EWM)
SG           18.20     95.00  SS EN 1993-1-3 (NA Singapore EWM)

Código no soportado: ValueError: código 'BR' no soportado
```

</details>

### 3. Distortional buckling of C and Z sections

#### C 200x60x20x2 purlin: AISI distortional buckling and the effect of the lip

Applicability, σ_crd and L_cr in compression and in bending (Appendix 2), and how σ_crd grows with the lip length. Until this version the module returned σ_crd of the order of 10⁶ MPa because of a dimensional inconsistency; it has been reimplemented and anchored by substitution by hand.

<details><summary>Actual output of <code>python examples/c_purlin_distortional_buckling_aisi_lip_size_sweep.py</code></summary>

```text
Sección C 200x60x20x2.0, f_y = 350 MPa
  Aplicabilidad DSM (AISI S100): sí []
  Aplicabilidad EN 1993-1-3:     sí []

Pandeo distorsional AISI S100:
  standard                     AISI S100-16/22
  method                       Direct Strength Method (DSM)
  units                        {'force': 'kN', 'moment': 'kNm', 'stress': 'MPa', 'length': 'mm'}
  sigma_crd_MPa                227.94
  L_crd_mm                     587.7
  sigma_crd_flex_MPa           556.02
  L_crd_flex_mm                531.4
  Py_kN                        252.0
  Pcrd_kN                      164.12
  lambda_d_c                   1.239
  Pnd_kN                       157.17
  phi_c_Pn_kN                  133.6
  My_kNm                       15.344
  Mcrd_kNm                     24.376
  lambda_d_b                   0.793
  Mnd_kNm                      13.977
  phi_b_Mn_kNm                 12.579
  is_valid_dsm                 True
  validity_notes               []

Efecto del labio rigidizador:
  labio [mm] | resultado
          10 | sigma_crd_MPa = 120.5, L_crd_mm = 362.3, sigma_crd_flex_MPa = 359.1
          15 | sigma_crd_MPa = 175.6, L_crd_mm = 480.7, sigma_crd_flex_MPa = 471.4
          20 | sigma_crd_MPa = 227.9, L_crd_mm = 587.7, sigma_crd_flex_MPa = 556
          25 | sigma_crd_MPa = 273.4, L_crd_mm = 685.8, sigma_crd_flex_MPa = 610.7
          30 | sigma_crd_MPa = 309.6, L_crd_mm = 777.5, sigma_crd_flex_MPa = 638.5
```

</details>

#### Z 250x75x20x2.5 purlin: AISI against EN 1993-1-3 §5.5.3

The intermediate values of each method (σ_crd, L_cr; K, σ_cr,s, λ̄_d, χ_d, t_red) and the capacities in compression and bending.

<details><summary>Actual output of <code>python examples/z_purlin_distortional_aisi_vs_ec3.py</code></summary>

```text
Z 250x75x20x2.5, f_y = 350 MPa, A = 1100 mm², S_f ≈ 83.5 cm³

AISI S100-16/22 — Direct Strength Method (DSM)
  σ_crd = 186.4 MPa, L_crd = 629 mm
  compresión: P_y = 385.0, P_crd = 205.1, λ_d = 1.370 → P_nd = 218.6 kN, φ_c·P_n = 185.8 kN
  flexión:    M_y = 29.23, M_crd = 40.98, λ_d = 0.845 → M_nd = 25.60 kN·m, φ_b·M_n = 23.04 kN·m
  válido DSM: True []

EN 1993-1-3:2006 — Effective Width Method (EWM §5.5.3 Edge Stiffener) (compression)
  K = 0.9303 N/mm², A_s = 143.8 mm², I_s = 4928 mm⁴
  σ_cr,s = 431.7 MPa, λ̄_d = 0.900, χ_d = 0.819, t_red = 2.047 mm
  N_c,Rd = 239.4 kN; válido EC3: True []
EN 1993-1-3:2006 — Effective Width Method (EWM §5.5.3 Edge Stiffener) (bending)
  K = 2.9096 N/mm², A_s = 143.8 mm², I_s = 4928 mm⁴
  σ_cr,s = 763.4 MPa, λ̄_d = 0.677, χ_d = 0.980, t_red = 2.451 mm
  M_c,Rd = 29.04 kN·m; válido EC3: True []
```

</details>

#### Edge stiffener: how much lip is needed for χ_d not to penalise

Sweep of the lip length in a 1.5 mm C 200x60, with the code warning when c/b leaves the recommended range.

<details><summary>Actual output of <code>python examples/ec3_edge_stiffener_chi_d_lip_length_sweep.py</code></summary>

```text
C 200x60xc x1,5, S350

c [mm]   c/b |        K  σ_cr,s   λ̄_d    χ_d  N_c,Rd | χ_d flex  M_c,Rd  avisos
     8  0.13 |   0.3566   155.9  1.498  0.441    76.8 |    0.652    9.34  Relación c/b = 0.13 fuera de la recomendación EN 1993-1-3 [0.2, 0.6]
    12  0.20 |   0.3566   246.7  1.191  0.609    85.4 |    0.820   10.25  —
    15  0.25 |   0.3566   311.6  1.060  0.704    91.4 |    0.891   10.73  —
    20  0.33 |   0.3566   372.3  0.970  0.769    96.6 |    0.941   11.27  —
    25  0.42 |   0.3566   391.7  0.945  0.787    98.2 |    0.954   11.63  —
    30  0.50 |   0.3566   404.5  0.930  0.797    99.3 |    0.962   11.94  —
```

</details>

#### Applicability limits: AISI Table B4.1-1 against EN 1993-1-3 Table 5.1

Six geometries, some deliberately out of range, with the warnings of each method.

<details><summary>Actual output of <code>python examples/applicability_limits_geometry_sweep.py</code></summary>

```text
C 200x60x20x2,0 (habitual): h/t = 100, b/t = 30, c/t = 10, h/b = 3.33, c/b = 0.33
   AISI DSM  válido: sin avisos
   EN 1993-1-3 válido: sin avisos
C 300x60x15x1,2 (alma muy esbelta): h/t = 250, b/t = 50, c/t = 12, h/b = 5.00, c/b = 0.25
   AISI DSM  NO válido: ['h/t = 250.0 excede el límite DSM de 200 para perfiles C/Z']
   EN 1993-1-3 válido: sin avisos
C 150x90x10x1,5 (ala ancha, labio corto): h/t = 100, b/t = 60, c/t = 7, h/b = 1.67, c/b = 0.11
   AISI DSM  válido: sin avisos
   EN 1993-1-3 válido: ['Relación c/b = 0.11 fuera de la recomendación EN 1993-1-3 [0.2, 0.6]']
Z 250x75x25x2,5: h/t = 100, b/t = 30, c/t = 10, h/b = 3.33, c/b = 0.33
   AISI DSM  válido: sin avisos
   EN 1993-1-3 válido: sin avisos
C 200x60x0x2,0 (sin labio): h/t = 100, b/t = 30, c/t = 0, h/b = 3.33, c/b = 0.00
   AISI DSM  NO válido: ['El perfil carece de pestaña (lip <= 0); no es aplicable pandeo distorsional de borde', 'Relación lip/b = 0.00 fuera del rango típico [0.05, 0.50]']
   EN 1993-1-3 NO válido: ['Perfil sin rigidizador de borde (c <= 0); aplicar §5.5.2 en vez de §5.5.3', 'Relación c/b = 0.00 fuera de la recomendación EN 1993-1-3 [0.2, 0.6]']
C 200x60x20x2,0 en f_y = 600: h/t = 100, b/t = 30, c/t = 10, h/b = 3.33, c/b = 0.33
   AISI DSM  NO válido: ['Fy = 600.0 MPa excede el límite de acero conformado en frío (550 MPa)']
   EN 1993-1-3 NO válido: ['fyb = 600.0 MPa excede los aceros normalizados de EN 1993-1-3']
```

</details>

#### Distortional capacity table of the catalogue sections

AISI φ_c·P_n and φ_b·M_n next to Eurocode N_c,Rd and M_c,Rd for the C and Z sections of the catalogue.

<details><summary>Actual output of <code>python examples/catalogue_profiles_distortional_capacity_table.py</code></summary>

```text
f_y = 350 MPa

perfil            kg/m | φP_n AISI φM_n AISI | N_c,Rd EC3 M_c,Rd EC3
AISI C8x2.5       3.92 |     106.2     11.22 |      145.8      14.83
AISI C10x2.5      5.16 |     135.3     19.99 |      204.9      25.51
AISI C12x3        7.24 |     219.7     37.01 |      310.8      45.91
EN C200x80x25     5.50 |     158.7     14.08 |      172.2      18.22
EN C250x80x25     7.85 |     212.6     24.83 |      257.6      31.06
AISI Z8x2.5       3.92 |     106.2     11.22 |      145.8      14.83
AISI Z10x3        5.85 |     239.5     29.84 |      310.8      35.96

* fuera de los límites de aplicabilidad de alguno de los métodos (ver applicability_limits_geometry_sweep.py)
Unidades: kN y kN·m. Los perfiles Σ del catálogo no se evalúan: los dos módulos cubren solo C y Z.
```

</details>

### 4. Local plate buckling and finite strips

#### Bryan critical stress for the four boundary conditions

Simply supported web (k = 4), outstand flange (0.425), fixed-fixed (6.97), fixed-simply supported (5.42) and an imposed k (23.9, pure bending).

<details><summary>Actual output of <code>python examples/plate_local_buckling_bryan_boundary_conditions.py</code></summary>

```text
t = 2.0 mm, E = 210 000 MPa, ν = 0,30

 b [mm]    b/t |    ss_ss  ss_free       cc       cs |   k=23,9
                   k=4.0  k=0.425   k=6.97   k=5.42
     50     25 |   1214.7    129.1   2116.7   1645.9 |   7258.0
    100     50 |    303.7     32.3    529.2    411.5 |   1814.5
    150     75 |    135.0     14.3    235.2    182.9 |    806.4
    200    100 |     75.9      8.1    132.3    102.9 |    453.6
    300    150 |     33.7      3.6     58.8     45.7 |    201.6

local_critical_stress(150, 2, 'ss_free') → σ_cr = 14.34 MPa, k = 0.425, b/t = 75, método: Bryan/Timoshenko (analitica)
Comparación con f_y = 350 MPa: por encima de la fila con σ_cr < 350 la placa pandea antes de plastificar.
```

</details>

#### Finite strips with Numba against Bryan: convergence and sweep diagnostics

Simply supported plate and outstand with 4, 8 and 16 strips; the error drops below 0.3 % and the sweep reports how many lengths converged.

<details><summary>Actual output of <code>python examples/fsm_jit_plate_convergence_vs_bryan.py</code></summary>

```text
Placa 120x1.5 mm, borde ss_ss: Bryan σ_cr = 118.625 MPa (k = 4.0)
   4 franjas: σ_cr = 118.650 MPa, k_ef = 4.0008, error +2.07e-04; barrido 60/60 longitudes convergidas
   8 franjas: σ_cr = 118.634 MPa, k_ef = 4.0003, error +7.96e-05; barrido 60/60 longitudes convergidas
  16 franjas: σ_cr = 118.634 MPa, k_ef = 4.0003, error +7.17e-05; barrido 60/60 longitudes convergidas

Placa 120x1.5 mm, borde ss_free: Bryan σ_cr = 12.604 MPa (k = 0.425)
   4 franjas: σ_cr = 12.638 MPa, k_ef = 0.4262, error +2.71e-03; barrido 60/60 longitudes convergidas
   8 franjas: σ_cr = 12.638 MPa, k_ef = 0.4262, error +2.71e-03; barrido 60/60 longitudes convergidas
  16 franjas: σ_cr = 12.638 MPa, k_ef = 0.4262, error +2.71e-03; barrido 60/60 longitudes convergidas
```

</details>

#### Signature curve of a C section: what the assembly captures and what it doesn't

One strip per element against four sub-strips (`refine_profile_strips`). The local minimum appears; the distortional and global ones do not.

<details><summary>Actual output of <code>python examples/fsm_signature_curve_c_section_modes.py</code></summary>

```text
  λ [mm] | 1 franja por elemento  | 4 subfranjas por eleme
    20.0 |                 1946.5 |                 1938.3
    31.9 |                  795.8 |                  786.3
    51.0 |                  349.9 |                  336.7
    81.4 |                  187.7 |                  165.8
   130.0 |                  154.2 |                  111.5
   207.5 |                  215.0 |                  122.1
   331.4 |                  421.7 |                  206.3
   529.1 |                  942.3 |                  437.7
   844.8 |                 2118.1 |                 1001.4
  1348.9 |                 4365.8 |                 2248.8
  2153.7 |                 7635.1 |                 4580.0
  3438.7 |                11276.8 |                 8027.4

1 franja por elemento (5 franjas, 6 nodos): mínimos detectados Local λ = 118 mm, σ = 153.5 MPa

4 subfranjas por elemento (20 franjas, 21 nodos): mínimos detectados Local λ = 157 mm, σ = 108.7 MPa

Referencias: alma aislada k = 4 → 75.9 MPa; AISI Apéndice 2 distorsional → 227.9 MPa a L_cr = 588 mm.
La curva FSM no presenta mínimo en torno a 590 mm ni se aplana a longitudes largas: este ensamblado solo es fiable para el modo local.
```

</details>

#### σ_cr(λ) curve of an isolated plate: k = (b/λ + λ/b)² and its minimum at λ = b

<details><summary>Actual output of <code>python examples/simplified_signature_curve_plate_k_vs_wavelength.py</code></summary>

```text
Placa 200x2.0 mm apoyada-apoyada; π²D/(b²t) = 18.980 MPa

 λ [mm]   λ/b  σ_cr [MPa]       k
     50  0.25      342.83  18.062
    100  0.50      118.63   6.250
    150  0.75       82.38   4.340
    200  1.00       75.92   4.000
    250  1.25       79.76   4.202
    300  1.50       89.10   4.694
    400  2.00      118.63   6.250
    600  3.00      210.89  11.111
   1000  5.00      513.22  27.040
   2000 10.00     1936.15 102.010

Mínimos etiquetados:
  Local         λ =   200.0 mm, σ_cr =    75.92 MPa
  Distortional  λ =  1000.0 mm, σ_cr =   513.22 MPa
  Global        λ =  2000.0 mm, σ_cr =  1936.15 MPa
```

</details>

#### Plate buckling surrogate model (`ml` extra): training, holdout and batch

With 2 000 samples the holdout R² is 0.97 and the pointwise error reaches 17 %: it is good for screening large sweeps, not for replacing the closed form on a specific plate.

<details><summary>Actual output of <code>python examples/surrogate_batch_prediction_vs_fsm.py</code></summary>

```text
Holdout: R² = 0.9718, MAE = 155.54 MPa (n_train = 1500, n_test = 500)

    b    t      k  σ_cr Bryan  σ_cr surrogate   error
  100  1.0  4.000       75.92           75.34   -0.8%
  150  2.0  4.000      134.97          153.71  +13.9%
  200  2.0  0.425        8.07            7.84   -2.8%
  250  3.0  4.000      109.32          113.98   +4.3%
   80  1.5  6.970      465.08          384.44  -17.3%
  300  2.5  5.420       71.44           76.36   +6.9%
```

</details>

### 5. Complementary checks (AISI S100)

#### Web shear (§G2): yielding, inelastic and elastic buckling

<details><summary>Actual output of <code>python examples/web_shear_capacity_aisi_g2_regimes.py</code></summary>

```text
t = 1.5 mm, f_y = 350 MPa, k_v = 5,34

h [mm]    h/t  V_y [kN]  V_cr [kN]    λ_v  V_n [kN]  régimen
   100     67     31.50      33.07  0.976     26.30  pandeo inelastico
   150    100     47.25      22.04  1.464     22.04  pandeo elastico
   200    133     63.00      16.53  1.952     16.53  pandeo elastico
   250    167     78.75      13.23  2.440     13.23  pandeo elastico
   300    200     94.50      11.02  2.928     11.02  pandeo elastico
   400    267    126.00       8.27  3.904      8.27  pandeo elastico

Con rigidizadores transversales k_v sube y el alma esbelta recupera cortante: pasa k_v en ShearInput.
```

</details>

#### Web crippling at the supports of a purlin (§G5)

End and interior support, one flange and two flanges, and the effect of the bearing length N and of the thickness.

<details><summary>Actual output of <code>python examples/purlin_web_crippling_support_reactions_aisi_g5.py</code></summary>

```text
C 250x75x20x2.0, f_y = 350, R = 3.0 mm, h = 250 mm, N = 60 mm

caso                              P_n [kN]  φP_n [kN]  coeficientes
stiffened_end_one_flange             10.51       7.88  EOF rigidizada
stiffened_interior_one_flange        20.52      15.39  IOF rigidizada
stiffened_end_two_flange              7.27       5.45  ETF rigidizada
stiffened_interior_two_flange        23.09      17.32  ITF rigidizada
unstiffened_end_one_flange           10.51       7.88  EOF no rigidizada

Apoyo interior, un ala: efecto de la longitud de apoyo N y del espesor t
N [mm] |    t=1.5    t=2.0    t=2.5    t=3.0
    40 |     7.77    14.16    22.40    32.48
    60 |     8.51    15.39    24.21    34.94
   100 |     9.67    17.33    27.07    38.86
   150 |    10.83    19.27    29.93    42.76
```

</details>

#### Bending-shear and axial-bending interaction (§H1) with capacities from the package itself

<details><summary>Actual output of <code>python examples/interaction_bending_shear_axial_bending_aisi_h1.py</code></summary>

```text
Capacidades de diseño: φM_n = 12.74 kN·m, φV_n = 37.99 kN, φP_n = 136.6 kN

Flexión + cortante (§H1.1, circular):
  M =   6.0 kN·m, V =  10.0 kN → ratio = 0.539 OK  [H1.1 (M-V)]
  M =   9.0 kN·m, V =  14.0 kN → ratio = 0.797 OK  [H1.1 (M-V)]
  M =  11.0 kN·m, V =  18.0 kN → ratio = 0.985 OK  [H1.1 (M-V)]

Axil + flexión (§H1.2, lineal):
  P =  20.0 kN, M =  3.0 kN·m → ratio = 0.382 OK  [H1.2 (P-M)]
  P =  40.0 kN, M =  5.0 kN·m → ratio = 0.685 OK  [H1.2 (P-M)]
  P =  60.0 kN, M =  6.0 kN·m → ratio = 0.910 OK  [H1.2 (P-M)]
```

</details>

#### Torsion of an open channel: J, Saint-Venant τ and warping constant

<details><summary>Actual output of <code>python examples/channel_torsion_saint_venant_and_warping.py</code></summary>

```text
Canal 200x75x2.5: J = 1822.9 mm⁴, C_w = 3.139e+09 mm⁶
 T [N·m]  τ_sv [MPa]  frente a 0,6·f_y = 210 MPa
      25        34.3  OK
      50        68.6  OK
     100       137.1  OK
     150       205.7  OK
     250       342.9  NO

Con J tan bajo, cargas fuera del centro de esfuerzos cortantes deben resistirse por alabeo o evitarse con arriostramiento: este chequeo solo acota la componente de Saint-Venant.
```

</details>

#### Web holes and yield strength reduction from galvanizing

Net area and reduction factor to AISI and EN, f_y adjusted by coating process, and zinc thickness to EN ISO 1461.

<details><summary>Actual output of <code>python examples/perforated_web_and_galvanized_yield_reductions.py</code></summary>

```text
Hueco d = 40 mm, separación 300 mm (d/w = 0.27):
  AISI  A_bruta = 225, A_neta = 148 mm², factor = 0.660, P_n = 59.4 kN  ['spacing <24d penaliza extra']
  EN    A_bruta = 225, A_neta = 165 mm², factor = 0.578, P_n = 52.0 kN  
Hueco d = 40 mm, separación 600 mm (d/w = 0.27):
  AISI  A_bruta = 225, A_neta = 148 mm², factor = 0.660, P_n = 59.4 kN  ['spacing <24d penaliza extra']
  EN    A_bruta = 225, A_neta = 165 mm², factor = 0.578, P_n = 52.0 kN  
Hueco d = 100 mm, separación 300 mm (d/w = 0.67):
  AISI  A_bruta = 225, A_neta = 68 mm², factor = 0.300, P_n = 27.0 kN  ['d/w>0.5 fuera de rango AISI estándar', 'spacing <24d penaliza extra']
  EN    A_bruta = 225, A_neta = 75 mm², factor = 0.193, P_n = 17.3 kN  ['d/w>0.6 fuera de rango EN 1993-1-3']

Límite elástico ajustado por recubrimiento (f_y = 350 MPa):
  hot_dip_galvanized   f_y,adj = 332.5 MPa
  electrogalvanized    f_y,adj = 343.0 MPa
  aluminized           f_y,adj = 339.5 MPa
  duplex               f_y,adj = 329.0 MPa
  painted              f_y,adj = 350.0 MPa

Espesor mínimo de zinc EN ISO 1461:
  t = 1.2 mm → 45 μm
  t = 2.0 mm → 55 μm
  t = 4.0 mm → 70 μm
  t = 8.0 mm → 85 μm
```

</details>

### 6. Catalogue, section properties, cost, export and API

#### From the catalogue to the SAP2000 Section Designer polygon

<details><summary>Actual output of <code>python examples/catalogue_to_sap2000_section_designer_polygon.py</code></summary>

```text
perfil           norma        forma      h     b labio    t   kg/m
AISI C8x2.5      AISI         C        203    64    13  2.0   3.92
AISI C10x2.5     AISI         C        254    64    13  2.5   5.16
AISI C12x3       AISI         C        305    76    19  3.0   7.24
AISI Z8x2.5      AISI         Z        203    64    13  2.0   3.92
AISI Z10x3       AISI         Z        254    76    19  3.0   5.85
EN Σ200x80x25    EN 1993-1-3  Sigma    200    80    25  2.5   6.18
EN Σ250x80x30    EN 1993-1-3  Sigma    250    80    30  3.0   8.39
EN Σ300x90x30    EN 1993-1-3  Sigma    300    90    30  3.5  11.50
EN C200x80x25    EN 1993-1-3  C        200    80    25  2.0   5.50
EN C250x80x25    EN 1993-1-3  C        250    80    25  2.5   7.85

EN C200x80x25: 12 puntos, t = 2.0 mm, material S350
  polígono (x, y) [mm]: [(0, 0), (80, 0), (80, 25), (78.0, 25), (78.0, 2.0), (2.0, 2.0), (2.0, 198.0), (78.0, 198.0), (78.0, 175), (80, 175), (80, 200), (0, 200)]
  push_to_sap(None, shape) sin fastsap → False
  lookup('no existe') → None
```

</details>

#### Properties of a channel with `sectionproperties`

<details><summary>Actual output of <code>python examples/channel_section_properties_sectionproperties.py</code></summary>

```text
C200x75x3.0: A = 1032 mm², I_xx = 6.192e+06 mm⁴, I_yy = 5.403e+05 mm⁴
  J = 3114.9 mm⁴, C_w = 3.715e+09 mm⁶, Z_xx,pl = 7.255e+04 mm³, r_xx = 77.5 mm, r_yy = 22.9 mm
  centroide: x = 17.2 mm, y = 100.0 mm  ['Channel d=200 b=75 tf=3.0 tw=3.0 mm', 'Area = 1032 mm2']

C250x80x2.5: A = 1012 mm², I_xx = 9.190e+06 mm⁴, I_yy = 5.770e+05 mm⁴
  J = 2118.0 mm⁴, C_w = 6.334e+09 mm⁶, Z_xx,pl = 8.702e+04 mm³, r_xx = 95.3 mm, r_yy = 23.9 mm
  centroide: x = 16.6 mm, y = 125.0 mm  ['Channel d=250 b=80 tf=2.5 tw=2.5 mm', 'Area = 1012 mm2']
```

</details>

#### Cost and CO₂ of a purlin order by country

Indicative rates included in the module: replace them with your quotes.

<details><summary>Actual output of <code>python examples/purlin_order_cost_and_co2_by_country.py</code></summary>

```text
país      USD/t ef.  peso [kg]  total USD   t CO₂
CL             2428       7920      19231   17.42
CO             2494       7920      19750   17.42
US             2034       7920      16112   14.26
EU             2231       7920      17672   12.67
AU             2691       7920      21310   15.05
SG             2297       7920      18191   14.26

Mismo pedido en perfil Σ (EU): 21445 USD (2.410 USD/kg)
```

</details>

#### REST API without a server, with FastAPI's TestClient

<details><summary>Actual output of <code>python examples/rest_api_section_and_winter_endpoints_testclient.py</code></summary>

```text
GET /api/coldformed/health → {'status': 'ok'}

POST /api/coldformed/section → 200 {"section_class": 4, "epsilon": 0.813617, "w_eff_cm3": 809.9}

POST /api/coldformed/effective-width/class4 (alma W00777) → 200
{
  "b_bar_mm": 1488.0,
  "t_mm": 10.0,
  "lambda_p": 1.3172429597410191,
  "rho": 0.6957655305820986,
  "b_eff_mm": 1035.2991095061627,
  "is_effective_reduced": true,
  "code": "EN 1993-1-5 §4.4 (Winter Eq. 4.2 / 4.3)"
}

t negativo → 422 (validación de entrada)
```

</details>

## Verification

- Winter's ρ factor is anchored to four worked examples of the UPC master's course (records W00777, W01486, W01527 and W01482), each with a different f_y, a different b/t ratio and, in W01486, a non-trivial ψ. The expected values are those of the records, recomputed by hand, not re-runs of the code.
- The critical plate stress matches Bryan/Timoshenko (§9.3) and the DSM in bending reproduces example 1 of Schafer (2008).
- AISI distortional buckling (Appendix 2) is anchored to the substitution by hand of the equations for a C 200x60x20x2 (σ_crd = 228 MPa, L_cr = 588 mm) and to consistency checks: the closed-form L_cr is the numerical minimum of F_crd(L), σ_crd grows with the lip and drops without it, and bracing shorter than L_cr raises it. The corpus has no published example with a numerical σ_crd; a comparison with CUFSM is pending.
- The finite-strip assembly reproduces the plate solution with an error below 0.3 % (`fsm_jit_plate_convergence_vs_bryan`).
- Fixes in this revision (1.1.0): `aisi_distortional_buckling` reimplemented with AISI S100-16 Appendix 2 (it previously mixed (π/L)² with (π/L)⁴ and omitted k̃_φwg: σ_crd ≈ 2.7·10⁶ MPa and the distortional mode never governed); new `refine_profile_strips` so that the FSM curve captures the local mode of wide webs.

## Limitations

- `fsm_assembly.compute_signature_curve_fsm` only reproduces the local mode: for a lipped C the distortional minimum does not appear, and at long lengths σ_cr grows instead of flattening towards Euler. Use Appendix 2 for σ_crd and Euler for the global mode.
- `distortional` covers C and Z with a simple 90° lip; in bending ξ_web = 2 (pure bending) is assumed. Centreline dimensions are taken as b − t and c − t/2.
- `shear` implements only AISI §G2; there is no V_b,Rd from EN 1993-1-3.
- `Class4Section` idealises the box or the I with a single thickness and fixed ψ (−1 web, +1 flange); it is an approximation, not a full effective section calculation.
- `signature_curve` (analytical module) is an isolated plate: its «Distortional» and «Global» labels are λ regions, not modes of a section.
- `web_crippling` includes five representative sets of coefficients from Table G5-1, not the five full tables.
- `perforations`, `galvanizing` and `cost_estimator` are simplified rules and indicative rates.
- The `surrogates` model has errors of the order of 10–20 % per point; it is a screening tool.
- `fsm_jit` compiles with Numba on the first call, which takes a few seconds.

## Codes and references

- EN 1993-1-3:2006, Eurocode 3, Part 1-3: Supplementary rules for cold-formed members and sheeting. §5.5.2, §5.5.3 (eq. 5.10–5.15), Table 5.1, §6.1.5, §10.
- EN 1993-1-5:2006, Part 1-5: Plated structural elements. §4.4 (eq. 4.2, 4.3), Tables 4.1 and 4.2.
- AISI S100-16 (2020) and S100-22, North American Specification for the Design of Cold-Formed Steel Structural Members: §E2–E4, §F2–F4, §G2, §G5, §H1, Appendix 2 (§2.3.1.3, §2.3.3.3, Table 2.3.1.3-1), Table B4.1-1.
- AS/NZS 4600:2018; NSR-10 Title F.4.
- Schafer, B. W. (2008), Review: The Direct Strength Method of cold-formed steel member design, J. Constr. Steel Res. 64; Schafer, B. W. and Peköz, T. (1999); Schafer, B. W. (2002), Local, distortional and Euler buckling of thin-walled columns, J. Struct. Eng. 128(3).
- Timoshenko, S. P. and Gere, J. M., Theory of Elastic Stability, 2nd ed., §9.3; Bryan, G. H. (1891).
- Hancock, G. J. (2006), Cold-Formed Steel Structures, 4th ed.; Cheung, Y. K. (1976), Finite Strip Method in Structural Analysis.
- EN ISO 1461 (hot-dip galvanizing), Table 3.
- Records of the Master's in Structural and Construction Engineering (UPC) cited by WorkID in the docstrings of `tests/`.

## License

MIT. See [LICENSE](LICENSE).

---

Part of **Loadpath**, the collection of open-source structural libraries by [Jesús Murgas](https://github.com/jmurgass99).
