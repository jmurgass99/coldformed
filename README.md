# coldformed

Diseño de acero conformado en frío y secciones de Clase 4: ancho eficaz (EN 1993-1-5 §4.4), Método de la Resistencia Directa (AISI S100), pandeo distorsional (AISI y EN 1993-1-3), método de las franjas finitas (FSM) con Numba, interacción, aplastamiento del alma y catálogo de perfiles.

[![CI](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Paquete independiente. Dependencias: `numpy`, `scipy`, `numba` y `sectionproperties`.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/coldformed.git
```

Extras: `api` (REST con FastAPI), `ml` (metamodelo sustituto del pandeo elástico con scikit-learn), `test`.

```bash
git clone https://github.com/jmurgass99/coldformed.git
cd coldformed
pip install -e ".[test,api,ml]"
pytest -q
```

## Inicio rápido

### Ancho eficaz de una placa interna comprimida (EN 1993-1-5 §4.4)

Alma de viga armada en flexión pura (ψ = −1, k_σ = 23,9), ejemplo anclado al trabajo W00777.

```python
from coldformed.class4_evaluator import plate_relative_slenderness, effective_width_factor_rho

lam_p = plate_relative_slenderness(b_bar=1500.0, t=10.0, fy=355.0, k_sigma=23.9)
rho = effective_width_factor_rho(lam_p, psi=-1.0)
print(round(lam_p, 3), round(rho, 2))   # 1.328  0.69
```

### Tensión crítica de pandeo local de una placa (franja finita, solución de Bryan)

```python
from coldformed.fsm_master_seed import FiniteStripMethodSeed

fsm = FiniteStripMethodSeed()
f_cr = fsm.calculate_plate_critical_stress(width=200, thickness=2)   # ≈ 72.3 MPa
```

### Método de la Resistencia Directa (AISI S100) en flexión

```python
from coldformed.direct_strength import DSMFlexureInput, dsm_flexure

res = dsm_flexure(DSMFlexureInput(Mcrl_kNm=9.0, Mcrd_kNm=10.5, Mcre_kNm=30.0, Sf_mm3=34000.0, Fy_MPa=350.0))
print(res.Mn_kNm, res.governing_mode)   # momento resistente nominal y modo que gobierna
```

## Módulos

| Módulo | Contenido |
|---|---|
| `class4_evaluator` | Esbeltez relativa de placa y factor ρ de Winter (EN 1993-1-5) |
| `effective_iter` | Iteración de ancho eficaz (AISI, EWM) |
| `direct_strength` | DSM en flexión y compresión (AISI S100) |
| `distortional` | Pandeo distorsional de C y Z según AISI y EN 1993-1-3 |
| `local_buckling`, `fsm`, `fsm_assembly`, `fsm_jit` | Tensión crítica local por franjas finitas, con ensamblaje acelerado con Numba |
| `signature_curve` | Curva de firma (local, distorsional, global) |
| `interaction`, `shear`, `web_crippling`, `torsion_open`, `perforations` | Verificaciones complementarias |
| `profile_catalog`, `galvanizing`, `cost_estimator` | Catálogo de perfiles, recubrimiento y coste |
| `surrogates` | Metamodelo sustituto del pandeo elástico (extra `ml`) |
| `sectprops_wrapper` | Propiedades de sección con `sectionproperties` |
| `codes_multi` | Despacho multinorma (EN 1993-1-3, AISI S100) |
| `api/` | REST API con FastAPI (extra `api`) |

El módulo `sap_section_bridge` exporta la geometría a SAP2000 solo si el cliente `fastsap` está instalado; sin él devuelve `False` sin lanzar error.

## Validación

El factor ρ está anclado a un ejemplo resuelto de viga armada de Clase 4 (ρ = 0,69); las pruebas de pandeo distorsional comprueban las condiciones de aplicabilidad de AISI y EN 1993-1-3; los tests de FSM comparan la solución de franjas con la solución cerrada de Bryan/Timoshenko. Consulta `docs/` para el alcance de lo verificado.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte del toolkit estructural de código abierto **Loadpath**, de [Jesús Murgas](https://github.com/jmurgass99).
