# coldformed

**Español** · [English](README.en.md)

Acero conformado en frío y secciones de clase 4: EN 1993-1-3, EN 1993-1-5 y AISI S100.

[![CI](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

## Qué hace

- Ancho eficaz de Winter y clasificación de secciones de clase 4 (EN 1993-1-5 §4.4).
- Método de la Resistencia Directa (AISI S100 / AS/NZS 4600) en flexión y compresión.
- Pandeo distorsional de perfiles C y Z (AISI S100 Apéndice 2 y EN 1993-1-3 §5.5.3).
- Tensión crítica de pandeo local de placa (Bryan y franjas finitas con Numba).
- Comprobaciones de una correa o un montante: cortante del alma, abolladura en apoyos, interacción, torsión, perforaciones y galvanizado.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/coldformed.git
```

Extras opcionales: `api`, `ml`.

## Ejemplo

Resistencia a flexión por el Método de la Resistencia Directa, con las cargas críticas de pandeo dadas (kN·m):

```python
from coldformed.direct_strength import DSMFlexureInput, dsm_flexure

r = dsm_flexure(DSMFlexureInput(Mcrl_kNm=9.0, Mcrd_kNm=10.5, Mcre_kNm=30.0,
                                Sf_mm3=34_000.0, Fy_MPa=350.0))
print(round(r.Mn_kNm, 2), r.governing_mode)   # 8.87 distortional
```

Más casos en [`examples/`](examples).

## Qué no hace

- Obtener esfuerzos: no hay análisis de barras ni de cargas.
- Los modos distorsional y global desde la curva de franjas finitas: el ensamblado actual reproduce el modo local.
- Perfiles Σ, omega o sombrero en los módulos distorsionales: cubren C y Z con labio simple.
- Pandeo lateral-torsional de la correa: M_cre se pasa como dato.

El detalle está en [docs/LIMITACIONES.md](docs/LIMITACIONES.md).

## Pruebas

```bash
pip install -e ".[test]"
pytest -q
```

## Licencia

MIT. Ver [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).
