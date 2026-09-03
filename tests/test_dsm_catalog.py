"""Tests DSM + catálogo perfiles."""
import pytest

from coldformedjm.direct_strength import (
    DSMFlexureInput, dsm_flexure, DSMCompressionInput, dsm_compression,
)
from coldformedjm.profile_catalog import lookup, list_profiles, to_cf_shape


class TestDSMFlexure:
    def test_compacto_no_reduce(self):
        # Mcrl alto → Mn = My
        r = dsm_flexure(DSMFlexureInput(
            Mcrl_kNm=1000, Mcrd_kNm=1000, Mcre_kNm=1000,
            Sf_mm3=200_000, Fy_MPa=350,
        ))
        assert r.Mn_kNm == r.My_kNm

    def test_local_gobierna_si_Mcrl_bajo(self):
        r = dsm_flexure(DSMFlexureInput(
            Mcrl_kNm=20, Mcrd_kNm=200, Mcre_kNm=200,
            Sf_mm3=200_000,
        ))
        assert r.governing_mode == "local"
        assert r.Mn_kNm < r.My_kNm

    @pytest.mark.parametrize("bad_val", [0.0, -10.0, float("nan")])
    def test_rejects_non_positive_or_nan_mcrl(self, bad_val):
        with pytest.raises(ValueError, match="estrictamente positivos y finitos"):
            dsm_flexure(DSMFlexureInput(
                Mcrl_kNm=bad_val, Mcrd_kNm=200.0, Mcre_kNm=200.0,
                Sf_mm3=200_000,
            ))


class TestDSMCompression:
    def test_compact(self):
        r = dsm_compression(DSMCompressionInput(
            Pcrl_kN=2000, Pcrd_kN=2000, Pcre_kN=2000, A_mm2=1000,
        ))
        assert r["Pn_kN"] > 0

    @pytest.mark.parametrize("bad_val", [0.0, -50.0, float("nan")])
    def test_rejects_non_positive_or_nan_pcrd(self, bad_val):
        with pytest.raises(ValueError, match="estrictamente positivas y finitas"):
            dsm_compression(DSMCompressionInput(
                Pcrl_kN=2000.0, Pcrd_kN=bad_val, Pcre_kN=2000.0, A_mm2=1000.0,
            ))


class TestCatalog:
    def test_lookup_existente(self):
        p = lookup("AISI C10x2.5")
        assert p is not None
        assert p.shape == "C"

    def test_list_filtrado(self):
        zs = list_profiles(shape="Z")
        assert all(p.shape == "Z" for p in zs)

    def test_to_cf_shape(self):
        shape = to_cf_shape("AISI C10x2.5")
        assert shape.thickness_mm > 0
        assert len(shape.points_mm) >= 4
