# coldformed — acero conformado en frío y secciones de Clase 4 (EN 1993-1-3/1-5, AISI S100)

Ancho eficaz de Winter y clasificación de secciones de Clase 4 (EN 1993-1-5 §4.4), Método de la Resistencia Directa en flexión y compresión (AISI S100 / AS/NZS 4600), pandeo distorsional de perfiles C y Z por AISI S100 Apéndice 2 y por EN 1993-1-3 §5.5.3 (rigidizador de borde), tensión crítica de pandeo local de placa (Bryan y franjas finitas con Numba), y las comprobaciones que acompañan a una correa o un montante: cortante del alma, abolladura en apoyos, interacción, torsión, perforaciones y galvanizado. Las funciones son puras y están ancladas a ejemplos resueltos a mano.

[![CI](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Qué problema resuelve

Tienes una correa, un montante o una viga armada de chapa delgada y necesitas saber cuánto de la sección trabaja de verdad (ancho eficaz), qué modo de pandeo gobierna (local, distorsional o global) y qué resistencia nominal y de diseño te queda según la norma del proyecto. El paquete resuelve esa parte con las fórmulas de las normas; los esfuerzos los traes de tu modelo.

**Úsalo cuando**

- clasifiques un alma o un ala comprimida y necesites ρ, λ_p y b_eff según EN 1993-1-5 §4.4, con ψ cualquiera;
- tengas las cargas o momentos críticos elásticos (de CUFSM, de la curva de franjas finitas del paquete o del Apéndice 2) y quieras la resistencia por el Método de la Resistencia Directa;
- diseñes correas C o Z y necesites el pandeo distorsional por AISI y por Eurocódigo, con sus límites de aplicabilidad;
- quieras la tensión crítica de una placa aislada (cuatro condiciones de borde) o verificar el ensamblado de franjas finitas contra la solución cerrada;
- compruebes cortante del alma (AISI §G2), abolladura en apoyos (§G5), interacción (§H1), torsión de Saint-Venant o reducción por huecos.

**No lo uses para**

- obtener esfuerzos: no hay análisis de barras ni de cargas;
- cortante del alma por EN 1993-1-3 §6.1.5: solo está AISI §G2;
- modos distorsional y global desde la curva de franjas finitas: el ensamblado actual reproduce el modo local y no muestra el mínimo distorsional ni el aplanamiento global (ver limitaciones); para σ_crd usa el Apéndice 2 y para el global, Euler o tu programa;
- perfiles Σ, omega o sombrero en los módulos distorsionales: cubren C y Z con labio simple;
- pandeo lateral-torsional de la correa (M_cre): se pasa como dato.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/coldformed.git
pip install "coldformed[api,ml] @ git+https://github.com/jmurgass99/coldformed.git"   # API REST y metamodelo scikit-learn
```

Dependencias: `numpy`, `scipy`, `numba` y `sectionproperties`. Para desarrollo: `git clone`, `pip install -e ".[test,api,ml]"`, `pytest -q` (27 ficheros de tests). En Windows, si la consola no es UTF-8, ejecuta los ejemplos con `python -X utf8 examples/<nombre>.py`.

## Capacidades

| Capacidad | Módulos | Norma o referencia | Casos de uso |
|---|---|---|---|
| Ancho eficaz y Clase 4: λ_p, ρ de Winter con ψ, clasificación y W_eff aproximado, iteración de propiedades eficaces, memoria de cálculo | `class4_evaluator`, `services.section_service`, `effective_iter`, `memos.aisi_effective_width` | EN 1993-1-5 §4.4 (ec. 4.2, 4.3, Tabla 4.1), EN 1993-1-3 §5.5.2 | [6 casos](#1-ancho-eficaz-y-secciones-de-clase-4-en-1993-1-5) |
| Método de la Resistencia Directa en flexión y compresión, factores φ/γ y despacho por norma (US, CO, AU, EU, SG) | `direct_strength`, `codes_multi` | AISI S100-16/22 §E2–E4, §F2–F4; AS/NZS 4600; NSR-10 F.4; EN 1993-1-3 | [5 casos](#2-método-de-la-resistencia-directa-y-despacho-multinorma) |
| Pandeo distorsional de C y Z: σ_crd y L_cr por Apéndice 2 (compresión y flexión), rigidizador de borde con muelle K y χ_d, límites de aplicabilidad | `distortional` | AISI S100-16 Apéndice 2 §2.3.1.3 y §2.3.3.3, Tabla B4.1-1; EN 1993-1-3 §5.5.3, Tabla 5.1 | [5 casos](#3-pandeo-distorsional-de-perfiles-c-y-z) |
| Pandeo local de placa: Bryan con cuatro condiciones de borde, franjas finitas con kernel Numba y curva de firma, metamodelo | `fsm`, `local_buckling`, `fsm_jit`, `fsm_assembly`, `signature_curve`, `surrogates` | Timoshenko & Gere §9.3; Schafer 2008 (CUFSM); Cheung 1976 | [5 casos](#4-pandeo-local-de-placa-y-franjas-finitas) |
| Comprobaciones complementarias: cortante del alma, abolladura en apoyos, interacción M-V y P-M, torsión de secciones abiertas, huecos, galvanizado | `shear`, `web_crippling`, `interaction`, `torsion_open`, `perforations`, `galvanizing` | AISI S100-16 §G2, §G5, §H1, §1.1.2; EN 1993-1-3 §10; EN ISO 1461 | [5 casos](#5-comprobaciones-complementarias-aisi-s100) |
| Catálogo de perfiles, propiedades con `sectionproperties`, coste y CO₂, polígono para SAP2000 y API REST | `profile_catalog`, `sectprops_wrapper`, `cost_estimator`, `sap_section_bridge`, `api` | — | [4 casos](#6-catálogo-propiedades-de-sección-coste-exportación-y-api) |

Los 30 scripts de `examples/` se ejecutaron en un entorno limpio antes de publicarse; su salida está en `examples/output/` y es la que se reproduce aquí.

## Casos de uso

### 1. Ancho eficaz y secciones de Clase 4 (EN 1993-1-5)

#### Viga armada de Clase 4: cuánto alma y cuánta ala trabajan

ρ de Winter del alma en flexión pura (ψ = −1, k_σ = 23,9) y del ala comprimida (ψ = +1, k_σ = 4) para varias esbelteces, y el caso de referencia del máster (ficha W00777): alma 1 488×10 en S355 → ρ = 0,69.

<details><summary>Salida real de <code>python examples/plate_girder_class4_web_flange_effective_width_en1993_1_5.py</code></summary>

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

#### Alma de correa C 200.74.2 bajo gradiente de tensiones (ψ = −0,74)

Exercise 16 del máster UPC (ficha W01486): k_σ por la fórmula de la Tabla 4.1 y ρ = 0,85. Con ψ equivocado o con la fórmula de voladizo no sale el resultado de la ficha.

<details><summary>Salida real de <code>python examples/exam_c200_purlin_web_stress_gradient_psi_w01486.py</code></summary>

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

#### Dos almas más del máster: CF 200.2 en S460 y Z 350.3 en S350GD

Fichas W01527 y W01482 con otro límite elástico y otra relación b/t que el caso de referencia. El de la Z es una afirmación a nivel de placa (la ficha no descuenta esquinas).

<details><summary>Salida real de <code>python examples/exam_cf200_s460_and_z350_webs_pure_bending_w01527_w01482.py</code></summary>

```text
caso                                      b/t      ε    λ_p      ρ | ficha λ_p / ρ
CF 200.2, S460 (W01527)                  99.0  0.715  0.998  0.892 | 1.00 / 0.890
Z 350.3, S350GD (W01482)                116.7  0.819  1.025  0.871 | 1.03 / 0.867
Viga armada 1488x10, S355 (W00777)      148.8  0.814  1.317  0.696 | 1.32 / 0.690

Las fichas redondean λ_p a dos decimales antes de evaluar ρ; la diferencia con el valor exacto es de 0,001 a 0,003 en ρ.
```

</details>

#### Cajón soldado: clase y módulo eficaz aproximado para varios espesores

`Class4Section` idealiza el cajón por b, h y un espesor único; `evaluate_section` lo envuelve con validación.

<details><summary>Salida real de <code>python examples/box_section_class_check_and_effective_modulus.py</code></summary>

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

#### Memoria de cálculo del ancho eficaz en Markdown y LaTeX

Los cuatro pasos (σ_cr, λ_p con la tensión actuante, ρ, b_eff) listos para un informe.

<details><summary>Salida real de <code>python examples/effective_width_memo_markdown.py</code></summary>

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

#### Iteración de propiedades eficaces con el modelo global

El modelo resuelve con sección bruta; cada reducción de ancho eficaz sube la tensión y obliga a reducir otra vez. El bucle converge en pocas iteraciones.

<details><summary>Salida real de <code>python examples/effective_properties_iteration_with_fem_demand.py</code></summary>

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

### 2. Método de la Resistencia Directa y despacho multinorma

#### Flexión: qué modo gobierna al variar M_crl y M_crd

Con M_y fijo, barrido de los momentos críticos local y distorsional para ver qué modo limita y cuánto penaliza.

<details><summary>Salida real de <code>python examples/dsm_flexure_mode_sweep_aisi_s100.py</code></summary>

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

#### Montante C en compresión: efecto de la longitud sin arriostrar

P_crl del alma, P_crd del Apéndice 2 y P_cre de Euler para cada longitud; el DSM devuelve el modo que gobierna.

<details><summary>Salida real de <code>python examples/dsm_compression_stud_column_unbraced_length_sweep.py</code></summary>

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

#### Montante C: local desde la curva FSM, distorsional desde el Apéndice 2, global de Euler

Cada carga crítica por la vía que el paquete resuelve bien, y después `dsm_compression`.

<details><summary>Salida real de <code>python examples/stud_dsm_local_from_fsm_distortional_from_appendix2.py</code></summary>

```text
C 200x60x20x2.0, A = 720 mm², L = 2400 mm
  local (FSM refinado):       σ_crl =  108.6 MPa a λ = 148 mm → P_crl = 78.2 kN
  distorsional (Apéndice 2):  σ_crd =  227.9 MPa a L_cr = 588 mm → P_crd = 164.1 kN
  global (Euler, I_min dato): P_cre = 107.9 kN

DSM: P_y = 252.0  P_ne = 94.7  P_nl = 75.5  P_nd = 157.2  →  P_n = 75.5 kN, gobierna local; φ_c·P_n = 64.2 kN
```

</details>

#### Capacidad de diseño por norma: AISI (US, CO, AU) frente a EN 1993-1-3 (EU, SG)

`design_capacity_cz` aplica DSM o el método del ancho eficaz según el código; no son el mismo método y los números lo muestran.

<details><summary>Salida real de <code>python examples/multicode_design_capacity_c_section_us_co_au_eu.py</code></summary>

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

#### Factores de resistencia por código

φ de AISI y AS/NZS frente a γ_M de Eurocódigo sobre una misma resistencia nominal.

<details><summary>Salida real de <code>python examples/resistance_factors_by_code_dsm_vs_ewm.py</code></summary>

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

### 3. Pandeo distorsional de perfiles C y Z

#### Correa C 200x60x20x2: pandeo distorsional AISI y efecto del labio

Aplicabilidad, σ_crd y L_cr en compresión y en flexión (Apéndice 2), y cómo crece σ_crd con la longitud del labio. Hasta esta versión el módulo daba σ_crd del orden de 10⁶ MPa por una inconsistencia dimensional; está reimplementado y anclado por sustitución a mano.

<details><summary>Salida real de <code>python examples/c_purlin_distortional_buckling_aisi_lip_size_sweep.py</code></summary>

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

#### Correa Z 250x75x20x2,5: AISI frente a EN 1993-1-3 §5.5.3

Los intermedios de cada método (σ_crd, L_cr; K, σ_cr,s, λ̄_d, χ_d, t_red) y las capacidades en compresión y flexión.

<details><summary>Salida real de <code>python examples/z_purlin_distortional_aisi_vs_ec3.py</code></summary>

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

#### Rigidizador de borde: cuánto labio hace falta para que χ_d no penalice

Barrido de la longitud del labio en una C 200x60 de 1,5 mm con el aviso de la norma cuando c/b sale del rango recomendado.

<details><summary>Salida real de <code>python examples/ec3_edge_stiffener_chi_d_lip_length_sweep.py</code></summary>

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

#### Límites de aplicabilidad: AISI Tabla B4.1-1 frente a EN 1993-1-3 Tabla 5.1

Seis geometrías, algunas fuera de rango a propósito, con los avisos de cada método.

<details><summary>Salida real de <code>python examples/applicability_limits_geometry_sweep.py</code></summary>

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

#### Tabla de capacidades distorsionales de los perfiles del catálogo

φ_c·P_n y φ_b·M_n de AISI junto a N_c,Rd y M_c,Rd de Eurocódigo para los C y Z del catálogo.

<details><summary>Salida real de <code>python examples/catalogue_profiles_distortional_capacity_table.py</code></summary>

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

### 4. Pandeo local de placa y franjas finitas

#### Tensión crítica de Bryan para las cuatro condiciones de borde

Alma apoyada (k = 4), ala en voladizo (0,425), empotrada-empotrada (6,97), empotrada-apoyada (5,42) y k impuesto (23,9, flexión pura).

<details><summary>Salida real de <code>python examples/plate_local_buckling_bryan_boundary_conditions.py</code></summary>

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

#### Franjas finitas con Numba frente a Bryan: convergencia y diagnóstico del barrido

Placa apoyada y voladizo con 4, 8 y 16 franjas; el error cae por debajo del 0,3 % y el barrido reporta cuántas longitudes convergieron.

<details><summary>Salida real de <code>python examples/fsm_jit_plate_convergence_vs_bryan.py</code></summary>

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

#### Curva de firma de una sección C: lo que el ensamblado captura y lo que no

Una franja por elemento frente a cuatro subfranjas (`refine_profile_strips`). Aparece el mínimo local; el distorsional y el global no.

<details><summary>Salida real de <code>python examples/fsm_signature_curve_c_section_modes.py</code></summary>

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

#### Curva σ_cr(λ) de una placa aislada: k = (b/λ + λ/b)² y su mínimo en λ = b

<details><summary>Salida real de <code>python examples/simplified_signature_curve_plate_k_vs_wavelength.py</code></summary>

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

#### Metamodelo de pandeo de placa (extra `ml`): entrenamiento, holdout y lote

Con 2 000 muestras el R² en holdout es 0,97 y el error por punto llega al 17 %: vale para cribar barridos grandes, no para sustituir la fórmula cerrada en una placa concreta.

<details><summary>Salida real de <code>python examples/surrogate_batch_prediction_vs_fsm.py</code></summary>

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

### 5. Comprobaciones complementarias (AISI S100)

#### Cortante del alma (§G2): fluencia, pandeo inelástico y elástico

<details><summary>Salida real de <code>python examples/web_shear_capacity_aisi_g2_regimes.py</code></summary>

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

#### Abolladura del alma en los apoyos de una correa (§G5)

Apoyo extremo e interior, un ala y dos alas, y el efecto de la longitud de apoyo N y del espesor.

<details><summary>Salida real de <code>python examples/purlin_web_crippling_support_reactions_aisi_g5.py</code></summary>

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

#### Interacción flexión-cortante y axil-flexión (§H1) con capacidades del propio paquete

<details><summary>Salida real de <code>python examples/interaction_bending_shear_axial_bending_aisi_h1.py</code></summary>

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

#### Torsión de un canal abierto: J, τ de Saint-Venant y constante de alabeo

<details><summary>Salida real de <code>python examples/channel_torsion_saint_venant_and_warping.py</code></summary>

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

#### Huecos en el alma y reducción del límite elástico por galvanizado

Área neta y factor de reducción según AISI y EN, f_y ajustado por proceso de recubrimiento y espesor de zinc EN ISO 1461.

<details><summary>Salida real de <code>python examples/perforated_web_and_galvanized_yield_reductions.py</code></summary>

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

### 6. Catálogo, propiedades de sección, coste, exportación y API

#### Del catálogo al polígono del Section Designer de SAP2000

<details><summary>Salida real de <code>python examples/catalogue_to_sap2000_section_designer_polygon.py</code></summary>

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

#### Propiedades de un canal con `sectionproperties`

<details><summary>Salida real de <code>python examples/channel_section_properties_sectionproperties.py</code></summary>

```text
C200x75x3.0: A = 1032 mm², I_xx = 6.192e+06 mm⁴, I_yy = 5.403e+05 mm⁴
  J = 3114.9 mm⁴, C_w = 3.715e+09 mm⁶, Z_xx,pl = 7.255e+04 mm³, r_xx = 77.5 mm, r_yy = 22.9 mm
  centroide: x = 17.2 mm, y = 100.0 mm  ['Channel d=200 b=75 tf=3.0 tw=3.0 mm', 'Area = 1032 mm2']

C250x80x2.5: A = 1012 mm², I_xx = 9.190e+06 mm⁴, I_yy = 5.770e+05 mm⁴
  J = 2118.0 mm⁴, C_w = 6.334e+09 mm⁶, Z_xx,pl = 8.702e+04 mm³, r_xx = 95.3 mm, r_yy = 23.9 mm
  centroide: x = 16.6 mm, y = 125.0 mm  ['Channel d=250 b=80 tf=2.5 tw=2.5 mm', 'Area = 1012 mm2']
```

</details>

#### Coste y CO₂ de un pedido de correas por país

Tarifas estimativas incluidas en el módulo: sustitúyelas por tus cotizaciones.

<details><summary>Salida real de <code>python examples/purlin_order_cost_and_co2_by_country.py</code></summary>

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

#### API REST sin servidor con el TestClient de FastAPI

<details><summary>Salida real de <code>python examples/rest_api_section_and_winter_endpoints_testclient.py</code></summary>

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

## Verificación

- El factor ρ de Winter está anclado a cuatro ejemplos resueltos del máster UPC (fichas W00777, W01486, W01527 y W01482), cada uno con otro f_y, otra relación b/t y, en W01486, un ψ no trivial. Los valores esperados son los de las fichas, recalculados a mano, no reejecuciones del código.
- La tensión crítica de placa coincide con Bryan/Timoshenko (§9.3) y el DSM en flexión reproduce el ejemplo 1 de Schafer (2008).
- El pandeo distorsional AISI (Apéndice 2) se ancla a la sustitución a mano de las ecuaciones para una C 200x60x20x2 (σ_crd = 228 MPa, L_cr = 588 mm) y a comprobaciones de consistencia: la L_cr cerrada es el mínimo numérico de F_crd(L), σ_crd crece con el labio y cae sin él, un arriostramiento más corto que L_cr lo sube. No hay en el corpus un ejemplo publicado con σ_crd numérico; un contraste con CUFSM queda pendiente.
- El ensamblado de franjas finitas reproduce la solución de placa con error menor del 0,3 % (`fsm_jit_plate_convergence_vs_bryan`).
- Correcciones de esta revisión (1.1.0): `aisi_distortional_buckling` reimplementado con AISI S100-16 Apéndice 2 (antes mezclaba (π/L)² con (π/L)⁴ y omitía k̃_φwg: σ_crd ≈ 2,7·10⁶ MPa y el modo distorsional nunca gobernaba); nuevo `refine_profile_strips` para que la curva FSM capture el modo local de almas anchas.

## Limitaciones

- `fsm_assembly.compute_signature_curve_fsm` solo reproduce el modo local: para una C con labios no aparece el mínimo distorsional y a longitudes largas σ_cr crece en vez de aplanarse hacia Euler. Usa el Apéndice 2 para σ_crd y Euler para el global.
- `distortional` cubre C y Z con labio simple a 90°; en flexión se asume ξ_web = 2 (flexión pura). Las dimensiones de línea media se toman como b − t y c − t/2.
- `shear` implementa solo AISI §G2; no hay V_b,Rd de EN 1993-1-3.
- `Class4Section` idealiza el cajón o la I con un espesor único y ψ fijos (−1 alma, +1 ala); es una aproximación, no un cálculo de sección eficaz completo.
- `signature_curve` (módulo analítico) es una placa aislada: sus etiquetas «Distortional» y «Global» son regiones de λ, no modos de una sección.
- `web_crippling` incluye cinco conjuntos representativos de coeficientes de la Tabla G5-1, no las cinco tablas completas.
- `perforations`, `galvanizing` y `cost_estimator` son reglas simplificadas y tarifas orientativas.
- El metamodelo `surrogates` tiene errores del orden del 10–20 % por punto; es una herramienta de cribado.
- `fatpack`-style cuantización no aplica aquí, pero `fsm_jit` compila con Numba en la primera llamada (unos segundos).

## Normas y referencias

- EN 1993-1-3:2006, Eurocódigo 3, Parte 1-3: Reglas suplementarias para perfiles y chapas de paredes delgadas conformadas en frío. §5.5.2, §5.5.3 (ec. 5.10–5.15), Tabla 5.1, §6.1.5, §10.
- EN 1993-1-5:2006, Parte 1-5: Placas planas cargadas en su plano. §4.4 (ec. 4.2, 4.3), Tablas 4.1 y 4.2.
- AISI S100-16 (2020) y S100-22, North American Specification for the Design of Cold-Formed Steel Structural Members: §E2–E4, §F2–F4, §G2, §G5, §H1, Apéndice 2 (§2.3.1.3, §2.3.3.3, Tabla 2.3.1.3-1), Tabla B4.1-1.
- AS/NZS 4600:2018; NSR-10 Título F.4.
- Schafer, B. W. (2008), Review: The Direct Strength Method of cold-formed steel member design, J. Constr. Steel Res. 64; Schafer, B. W. y Peköz, T. (1999); Schafer, B. W. (2002), Local, distortional and Euler buckling of thin-walled columns, J. Struct. Eng. 128(3).
- Timoshenko, S. P. y Gere, J. M., Theory of Elastic Stability, 2.ª ed., §9.3; Bryan, G. H. (1891).
- Hancock, G. J. (2006), Cold-Formed Steel Structures, 4.ª ed.; Cheung, Y. K. (1976), Finite Strip Method in Structural Analysis.
- EN ISO 1461 (galvanizado en caliente), Tabla 3.
- Fichas del máster de Ingeniería Estructural y de la Construcción (UPC) citadas por WorkID en los docstrings de `tests/`.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte de **Loadpath**, la colección de librerías estructurales de código abierto de [Jesús Murgas](https://github.com/jmurgass99).
