# coldformed

[Español](README.md) · **English**

Cold-formed steel and class 4 sections: EN 1993-1-3, EN 1993-1-5 and AISI S100.

[![CI](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/coldformed/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

- Winter effective width and class 4 section classification (EN 1993-1-5 §4.4).
- Direct Strength Method (AISI S100 / AS/NZS 4600) in flexure and compression.
- Distortional buckling of C and Z sections (AISI S100 Appendix 2 and EN 1993-1-3 §5.5.3).
- Local plate buckling stress (Bryan and finite strips with Numba).
- Purlin and stud checks: web shear, web crippling, interaction, torsion, perforations and galvanizing.

## Install

```bash
pip install git+https://github.com/jmurgass99/coldformed.git
```

Optional extras: `api`, `ml`.

## Example

Flexural strength by the Direct Strength Method, given the critical buckling moments (kN·m):

```python
from coldformed.direct_strength import DSMFlexureInput, dsm_flexure

r = dsm_flexure(DSMFlexureInput(Mcrl_kNm=9.0, Mcrd_kNm=10.5, Mcre_kNm=30.0,
                                Sf_mm3=34_000.0, Fy_MPa=350.0))
print(round(r.Mn_kNm, 2), r.governing_mode)   # 8.87 distortional
```

More cases in [`examples/`](examples).

## What it does not do

- Obtain internal forces: there is no member or load analysis.
- Distortional and global modes from the finite-strip curve: the current assembly reproduces the local mode.
- Σ, omega or hat sections in the distortional modules: they cover C and Z with a simple lip.
- Lateral-torsional buckling of the purlin: M_cre is an input.

Details are in [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (in Spanish).

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

## License

MIT. See [LICENSE](LICENSE). Author: [Jesús Murgas](https://github.com/jmurgass99).
