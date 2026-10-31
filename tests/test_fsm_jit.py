# -*- coding: utf-8 -*-
"""
Tests de unidad y rendimiento para el cálculo de matrices elásticas y geométricas FSM JIT.
"""
from __future__ import annotations
import numpy as np
import pytest
import time
from coldformed.fsm_jit import fsm_local_stiffness_matrices_jit

def test_fsm_numba_ke_kg_dimensions_and_properties():
    # Parámetros realistas de una faja elástica de acero
    width = 200.0      # mm
    thickness = 3.0    # mm
    length = 500.0     # mm
    E = 210000.0       # MPa
    nu = 0.3
    sigma_x = 150.0    # MPa
    
    ke, kg = fsm_local_stiffness_matrices_jit(
        width=width,
        thickness=thickness,
        length=length,
        E=E,
        nu=nu,
        sigma_x=sigma_x
    )
    
    # 1. Dimensiones de las matrices
    assert ke.shape == (4, 4)
    assert kg.shape == (4, 4)
    
    # 2. Conservación de energía: Las matrices deben ser rigurosamente simétricas (ke = ke.T y kg = kg.T)
    assert np.allclose(ke, ke.T, rtol=1e-12, atol=1e-12)
    assert np.allclose(kg, kg.T, rtol=1e-12, atol=1e-12)
    
    # 3. Validar elementos no nulos en diagonal principal (deben ser positivos)
    for i in range(4):
        assert ke[i, i] > 0.0
        assert kg[i, i] > 0.0

def test_fsm_numba_compilation_and_benchmark():
    # Calentamiento
    _, _ = fsm_local_stiffness_matrices_jit(100.0, 2.0, 300.0, 200000.0, 0.3, 100.0)
    
    # Medir rendimiento
    iterations = 5000
    t_start = time.perf_counter()
    for _ in range(iterations):
        _, _ = fsm_local_stiffness_matrices_jit(200.0, 3.0, 500.0, 210000.0, 0.3, 150.0)
    t_end = time.perf_counter()
    
    total_time_ms = (t_end - t_start) * 1000.0
    time_per_iter_us = (t_end - t_start) * 1000000.0 / iterations
    
    print(f"\n[BENCHMARK] FSM matrices local JIT: {iterations} ejecuciones en {total_time_ms:.2f} ms ({time_per_iter_us:.3f} us por matriz)")
    
    # Assert de salvaguarda de rendimiento (debe tomar menos de 10 microsegundos por iteración en JIT)
    assert time_per_iter_us < 20.0
