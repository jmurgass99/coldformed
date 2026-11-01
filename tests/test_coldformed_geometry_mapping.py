from __future__ import annotations

from coldformed.geometry_mapping import build_lipped_c_strip_mesh


def test_build_lipped_c_strip_mesh_geometry_mapping():
    m = build_lipped_c_strip_mesh(h_mm=200.0, b_mm=75.0, c_lip_mm=20.0, t_mm=2.0, divisions_per_wall=4)
    # 5 walls * 4 strips = 20 strips, 21 nodes
    assert len(m.strips) == 20
    assert len(m.nodes_yz_mm) == 21
    assert set(m.wall_to_strips.keys()) == {
        "bottom_lip", "bottom_flange", "web", "top_flange", "top_lip"
    }
    assert len(m.wall_to_strips["web"]) == 4
    assert m.corner_to_nodes["bot_lip_tip"] == 0
    assert m.corner_to_nodes["top_lip_tip"] == 20
