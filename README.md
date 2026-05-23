# ColdFormedJm

Diseno de acero conformado en frio

[![CI](https://github.com/jmurgass99/coldformedjm/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/coldformedjm/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-75.65%25-green?style=flat)](https://github.com/jmurgass99/coldformedjm)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

## Overview

Diseno de acero conformado en frio. Parte del ecosistema **jmurgass99** de herramientas de ingenieria estructural.

## Installation

```bash
git clone https://github.com/jmurgass99/coldformedjm.git
cd coldformedjm
pip install -e .
# Optional extras:
pip install -e ".[test,api]"
```

## Quick start

```python
from coldformedjm import *  # see examples/ for usage
```

## REST API (if available)

```bash
uvicorn coldformedjm.api.app:app --reload
# Open http://localhost:8000/docs
```

## Testing

```bash
pytest -q                                # quick suite
pytest -m "not slow"                     # exclude slow tests
.\scripts\run_coverage.ps1               # coverage with gate
```

## Project structure

```
coldformedjm/
  services/       # service layer (pure functions)
  api/            # FastAPI app (REST endpoints)
  exceptions.py   # typed exception hierarchy
  _brand.py       # brand constants
tests/            # pytest suite
```

## Ecosystem

This project is part of the **jmurgass99 structural engineering ecosystem**:

- [fastsap](https://github.com/jmurgass99/fastsap) - orquestador SAP2000/ETABS
- [dynamicsjmpro](https://github.com/jmurgass99/dynamicsjmpro) - SaaS frontend + backend
- [dynamicsjm](https://github.com/jmurgass99/dynamicsjm) - motor dinamico
- [foundationdesignjm](https://github.com/jmurgass99/foundationdesignjm) - cimentaciones
- [windloadjm](https://github.com/jmurgass99/windloadjm) - cargas de viento
- [seismicrecordsjm](https://github.com/jmurgass99/seismicrecordsjm) - records sismicos
- [slopestabilityjm](https://github.com/jmurgass99/slopestabilityjm) - estabilidad de taludes
- [steelconnectionjm](https://github.com/jmurgass99/steelconnectionjm) - conexiones de acero
- [steeloptimizerjm](https://github.com/jmurgass99/steeloptimizerjm) - optimizacion GA
- [coldformedjm](https://github.com/jmurgass99/coldformedjm) - acero conformado en frio
- [fatiguejm](https://github.com/jmurgass99/fatiguejm) - analisis de fatiga
- [firesteeljm](https://github.com/jmurgass99/firesteeljm) - analisis termico al fuego
- [dxfstructuraljm](https://github.com/jmurgass99/dxfstructuraljm) - generacion DXF


## Master IEG Integrations

Modulo `coldformedjm.fsm_master_seed` (integrado 2026-05-19 desde
`NEW CODES/STRUCTURAL/Master_IEG_Integrations/cold_formed_fsm.py`):

- `FiniteStripMethodSeed` — FSM-base (IEG 3120) con la solucion cerrada
  de Bryan/Timoshenko para pandeo elastico local de placa simple.
  Convive con `coldformedjm.fsm` (version full con multiples franjas);
  esta semilla se mantiene como referencia docente / quick-look.

```python
from coldformedjm.fsm_master_seed import FiniteStripMethodSeed
fsm = FiniteStripMethodSeed()
fcr = fsm.calculate_plate_critical_stress(width=200, thickness=2)
```

## License

Proprietary - (c) 2026 jmurgass99. All rights reserved.
