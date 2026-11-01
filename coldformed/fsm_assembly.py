"""
Finite Strip Method (FSM) -- Multi-strip assembly for cold-formed steel
profiles.  Full eigenvalue-based buckling analysis following Schafer (2008),
CUFSM theory manual, and Hancock (2006).

This module assembles elastic (K_E) and geometric (K_G) stiffness matrices
from multiple plate strips connected at shared nodes, solves the generalised
eigenvalue problem K_E * phi = lambda * K_G * phi for each half-wavelength,
and produces the signature curve (sigma_cr vs half-wavelength) with
automatic detection of local, distortional, and global minima.

References
----------
    Schafer, B.W. (2008)  -- CUFSM and the Direct Strength Method.
    Hancock, G.J. (2006)  -- Cold-Formed Steel Structures, 4th ed.
    Cheung, Y.K. (1976)   -- Finite Strip Method in Structural Analysis.
    EN 1993-1-5 sec.4     -- Compressed plate elements.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from scipy.linalg import eig


# ------------------------------------------------------------------
# Reuse the JIT-accelerated 4x4 bending matrices from fsm_jit.py
# ------------------------------------------------------------------
from coldformed.fsm_jit import fsm_local_stiffness_matrices_jit
from coldformed.signature_curve import SignatureResult


# ======================================================================
# Data classes
# ======================================================================

@dataclass
class StripDefinition:
    """One plate strip between two adjacent nodes.

    Attributes
    ----------
    width_mm : float
        Width *b* of the strip (centre-line distance between nodes).
    thickness_mm : float
        Plate thickness *t*.
    E_MPa : float
        Young's modulus.
    nu : float
        Poisson's ratio.
    stress_distribution : Literal["uniform", "linear"]
        Type of longitudinal stress across the strip width.
    connectivity : tuple[int, int]
        Global node indices (i, j) that bound this strip.
    """
    width_mm: float
    thickness_mm: float
    E_MPa: float = 210_000.0
    nu: float = 0.30
    stress_distribution: Literal["uniform", "linear"] = "uniform"
    connectivity: tuple[int, int] = (0, 1)


@dataclass
class ProfileStrips:
    """Complete discretisation of a cross-section into strips and nodes.

    Attributes
    ----------
    strips : list[StripDefinition]
        Ordered list of plate strips.
    node_coords : list[tuple[float, float]]
        Cross-section coordinates (y, z) of each node.
    """
    strips: list[StripDefinition] = field(default_factory=list)
    node_coords: list[tuple[float, float]] = field(default_factory=list)

    @property
    def n_nodes(self) -> int:
        return len(self.node_coords)

    @property
    def n_strips(self) -> int:
        return len(self.strips)

    @property
    def n_dof(self) -> int:
        """Total DOFs: 4 per node (u, v, w, theta)."""
        return 4 * self.n_nodes


# ======================================================================
# Profile factory
# ======================================================================

def build_profile_strips(
    profile_type: str,
    dims: dict[str, float],
) -> ProfileStrips:
    """Create strip definitions for standard cold-formed profiles.

    Parameters
    ----------
    profile_type : str
        One of ``"C"`` (channel), ``"Z"`` (zed), ``"hat"``, ``"sigma"``.
    dims : dict
        Profile dimensions.  Expected keys depend on the type:

        * C / Z: ``H`` (height), ``B`` (flange), ``D`` (lip), ``t``
          (thickness), and optionally ``E`` and ``nu``.
        * hat: ``H``, ``B_top``, ``B_bot``, ``D`` (lip, optional), ``t``.
        * sigma: ``H``, ``B``, ``D``, ``h_s`` (stiffener depth), ``t``.

    Returns
    -------
    ProfileStrips
    """
    ptype = profile_type.upper().strip()
    t = dims["t"]
    E = dims.get("E", 210_000.0)
    nu = dims.get("nu", 0.30)

    if ptype == "C":
        return _build_c_channel(dims, t, E, nu)
    elif ptype == "Z":
        return _build_z_section(dims, t, E, nu)
    elif ptype == "HAT":
        return _build_hat_section(dims, t, E, nu)
    elif ptype == "SIGMA":
        return _build_sigma_section(dims, t, E, nu)
    else:
        raise ValueError(
            f"profile_type '{profile_type}' not recognised; "
            f"valid types: C, Z, hat, sigma"
        )


def refine_profile_strips(strips: ProfileStrips, n_sub: int = 4) -> ProfileStrips:
    """Subdivide cada franja en ``n_sub`` franjas iguales añadiendo nodos intermedios.

    Una sola franja por elemento plano no puede flectar transversalmente en
    media onda, así que el modo local de un alma o un ala anchos sale muy
    rígido (para una C 200x60x20x2 el mínimo local pasa de 154 MPa con una
    franja por elemento a 109 MPa con 4 subfranjas). Los nodos nuevos se
    añaden al final de ``node_coords``; la conectividad los referencia por
    índice, así que el ensamblado no exige nodos contiguos.
    """
    if n_sub < 1:
        raise ValueError("n_sub debe ser >= 1")
    if n_sub == 1:
        return strips
    nodes = list(strips.node_coords)
    out: list[StripDefinition] = []
    for s in strips.strips:
        i, j = s.connectivity
        (x0, y0), (x1, y1) = nodes[i], nodes[j]
        prev = i
        for k in range(1, n_sub + 1):
            if k < n_sub:
                nodes.append((x0 + (x1 - x0) * k / n_sub, y0 + (y1 - y0) * k / n_sub))
                nxt = len(nodes) - 1
            else:
                nxt = j
            out.append(StripDefinition(
                width_mm=s.width_mm / n_sub, thickness_mm=s.thickness_mm, E_MPa=s.E_MPa, nu=s.nu,
                stress_distribution=s.stress_distribution, connectivity=(prev, nxt),
            ))
            prev = nxt
    return ProfileStrips(strips=out, node_coords=nodes)


def _strip(w: float, t: float, E: float, nu: float,
           conn: tuple[int, int]) -> StripDefinition:
    return StripDefinition(
        width_mm=w, thickness_mm=t, E_MPa=E, nu=nu,
        connectivity=conn,
    )


def _build_c_channel(d: dict, t: float, E: float, nu: float) -> ProfileStrips:
    """C-channel: bottom lip - bottom flange - web - top flange - top lip.

    Node layout (centre-line):
        0: bottom lip tip
        1: bottom lip/flange junction
        2: bottom flange/web junction
        3: top flange/web junction
        4: top flange/lip junction
        5: top lip tip
    """
    H, B, D = d["H"], d["B"], d.get("D", 0.0)
    nodes: list[tuple[float, float]] = []
    strips: list[StripDefinition] = []

    has_lips = D > 0

    if has_lips:
        # Node 0 -- bottom lip tip
        nodes.append((0.0, -D))
        # Node 1 -- bottom flange/lip junction
        nodes.append((0.0, 0.0))
        # Node 2 -- web bottom (bottom flange/web junction)
        nodes.append((B, 0.0))
        # Node 3 -- web top (top flange/web junction)
        nodes.append((B, H))
        # Node 4 -- top flange/lip junction
        nodes.append((0.0, H))
        # Node 5 -- top lip tip
        nodes.append((0.0, H + D))

        strips.append(_strip(D, t, E, nu, (0, 1)))   # bottom lip
        strips.append(_strip(B, t, E, nu, (1, 2)))   # bottom flange
        strips.append(_strip(H, t, E, nu, (2, 3)))   # web
        strips.append(_strip(B, t, E, nu, (3, 4)))   # top flange
        strips.append(_strip(D, t, E, nu, (4, 5)))   # top lip
    else:
        # No lips: 4 nodes
        nodes.append((0.0, 0.0))         # 0: bottom flange tip
        nodes.append((B, 0.0))           # 1: web bottom
        nodes.append((B, H))             # 2: web top
        nodes.append((0.0, H))           # 3: top flange tip

        strips.append(_strip(B, t, E, nu, (0, 1)))   # bottom flange
        strips.append(_strip(H, t, E, nu, (1, 2)))   # web
        strips.append(_strip(B, t, E, nu, (2, 3)))   # top flange

    return ProfileStrips(strips=strips, node_coords=nodes)


def _build_z_section(d: dict, t: float, E: float, nu: float) -> ProfileStrips:
    """Z-section: bottom flange extends one way, top flange the other.

    Node layout:
        0: bottom lip tip   (optional)
        1: bottom flange tip / lip junction
        2: web bottom
        3: web top
        4: top flange tip / lip junction
        5: top lip tip       (optional)
    """
    H, B, D = d["H"], d["B"], d.get("D", 0.0)
    nodes: list[tuple[float, float]] = []
    strips: list[StripDefinition] = []

    has_lips = D > 0

    if has_lips:
        nodes.append((-B, -D))      # 0 bottom lip tip
        nodes.append((-B, 0.0))     # 1 bottom flange tip
        nodes.append((0.0, 0.0))    # 2 web bottom
        nodes.append((0.0, H))      # 3 web top
        nodes.append((B, H))        # 4 top flange tip
        nodes.append((B, H + D))    # 5 top lip tip

        strips.append(_strip(D, t, E, nu, (0, 1)))   # bottom lip
        strips.append(_strip(B, t, E, nu, (1, 2)))   # bottom flange
        strips.append(_strip(H, t, E, nu, (2, 3)))   # web
        strips.append(_strip(B, t, E, nu, (3, 4)))   # top flange
        strips.append(_strip(D, t, E, nu, (4, 5)))   # top lip
    else:
        nodes.append((-B, 0.0))     # 0 bottom flange tip
        nodes.append((0.0, 0.0))    # 1 web bottom
        nodes.append((0.0, H))      # 2 web top
        nodes.append((B, H))        # 3 top flange tip

        strips.append(_strip(B, t, E, nu, (0, 1)))
        strips.append(_strip(H, t, E, nu, (1, 2)))
        strips.append(_strip(B, t, E, nu, (2, 3)))

    return ProfileStrips(strips=strips, node_coords=nodes)


def _build_hat_section(d: dict, t: float, E: float, nu: float) -> ProfileStrips:
    """Hat section: two webs with a top flange and bottom flanges.

    Node layout:
        0: bottom-left lip tip   (optional)
        1: bottom-left flange end
        2: web bottom-left
        3: web top-left / top flange left
        4: web top-right / top flange right
        5: web bottom-right
        6: bottom-right flange end
        7: bottom-right lip tip  (optional)
    """
    H = d["H"]
    B_top = d["B_top"]
    B_bot = d["B_bot"]
    D = d.get("D", 0.0)

    nodes: list[tuple[float, float]] = []
    strips: list[StripDefinition] = []
    has_lips = D > 0

    if has_lips:
        nodes.append((-B_bot, -D))       # 0
        nodes.append((-B_bot, 0.0))      # 1
        nodes.append((0.0, 0.0))         # 2
        nodes.append((0.0, H))           # 3
        nodes.append((B_top, H))         # 4
        nodes.append((B_top, 0.0))       # 5
        nodes.append((B_top + B_bot, 0.0))  # 6
        nodes.append((B_top + B_bot, -D))   # 7

        strips.append(_strip(D, t, E, nu, (0, 1)))
        strips.append(_strip(B_bot, t, E, nu, (1, 2)))
        strips.append(_strip(H, t, E, nu, (2, 3)))
        strips.append(_strip(B_top, t, E, nu, (3, 4)))
        strips.append(_strip(H, t, E, nu, (4, 5)))
        strips.append(_strip(B_bot, t, E, nu, (5, 6)))
        strips.append(_strip(D, t, E, nu, (6, 7)))
    else:
        nodes.append((-B_bot, 0.0))      # 0
        nodes.append((0.0, 0.0))         # 1
        nodes.append((0.0, H))           # 2
        nodes.append((B_top, H))         # 3
        nodes.append((B_top, 0.0))       # 4
        nodes.append((B_top + B_bot, 0.0))  # 5

        strips.append(_strip(B_bot, t, E, nu, (0, 1)))
        strips.append(_strip(H, t, E, nu, (1, 2)))
        strips.append(_strip(B_top, t, E, nu, (2, 3)))
        strips.append(_strip(H, t, E, nu, (3, 4)))
        strips.append(_strip(B_bot, t, E, nu, (4, 5)))

    return ProfileStrips(strips=strips, node_coords=nodes)


def _build_sigma_section(d: dict, t: float, E: float, nu: float) -> ProfileStrips:
    """Sigma section: like a C but with a web stiffener (fold).

    Node layout:
        0: bottom lip tip (opt)
        1: bottom flange end
        2: web bottom
        3: stiffener bottom
        4: stiffener tip
        5: stiffener top
        6: web top
        7: top flange end
        8: top lip tip (opt)
    """
    H, B, D = d["H"], d["B"], d.get("D", 0.0)
    h_s = d["h_s"]  # stiffener depth (horizontal indentation)

    nodes: list[tuple[float, float]] = []
    strips: list[StripDefinition] = []
    has_lips = D > 0

    half_H = H / 2.0
    stiff_half = h_s  # stiffener height symmetric about mid-web
    seg_web = (H - 2 * stiff_half) / 2.0  # web segment above/below stiffener

    if has_lips:
        nodes.append((0.0, -D))                        # 0  bottom lip tip
        nodes.append((0.0, 0.0))                       # 1  bottom flange
        nodes.append((B, 0.0))                         # 2  web bottom
        nodes.append((B, seg_web))                      # 3  stiffener bottom
        nodes.append((B - h_s, half_H))                # 4  stiffener tip
        nodes.append((B, H - seg_web))                  # 5  stiffener top
        nodes.append((B, H))                            # 6  web top
        nodes.append((0.0, H))                          # 7  top flange
        nodes.append((0.0, H + D))                      # 8  top lip tip

        strips.append(_strip(D, t, E, nu, (0, 1)))
        strips.append(_strip(B, t, E, nu, (1, 2)))
        s_web_bottom = math.hypot(0, seg_web)
        strips.append(_strip(s_web_bottom, t, E, nu, (2, 3)))
        s_stiff1 = math.hypot(h_s, half_H - seg_web)
        strips.append(_strip(s_stiff1, t, E, nu, (3, 4)))
        s_stiff2 = math.hypot(h_s, half_H - seg_web)
        strips.append(_strip(s_stiff2, t, E, nu, (4, 5)))
        s_web_top = math.hypot(0, seg_web)
        strips.append(_strip(s_web_top, t, E, nu, (5, 6)))
        strips.append(_strip(B, t, E, nu, (6, 7)))
        strips.append(_strip(D, t, E, nu, (7, 8)))
    else:
        nodes.append((0.0, 0.0))                       # 0  bottom flange
        nodes.append((B, 0.0))                         # 1  web bottom
        nodes.append((B, seg_web))                      # 2  stiffener bottom
        nodes.append((B - h_s, half_H))                # 3  stiffener tip
        nodes.append((B, H - seg_web))                  # 4  stiffener top
        nodes.append((B, H))                            # 5  web top
        nodes.append((0.0, H))                          # 6  top flange

        strips.append(_strip(B, t, E, nu, (0, 1)))
        s_web_bottom = math.hypot(0, seg_web)
        strips.append(_strip(s_web_bottom, t, E, nu, (1, 2)))
        s_stiff1 = math.hypot(h_s, half_H - seg_web)
        strips.append(_strip(s_stiff1, t, E, nu, (2, 3)))
        strips.append(_strip(s_stiff1, t, E, nu, (3, 4)))
        strips.append(_strip(s_web_bottom, t, E, nu, (4, 5)))
        strips.append(_strip(B, t, E, nu, (5, 6)))

    return ProfileStrips(strips=strips, node_coords=nodes)


# ======================================================================
# Strip rotation (local -> global in the cross-section plane)
# ======================================================================

def _strip_angle(ps: ProfileStrips, strip: StripDefinition) -> float:
    """Angle beta of the strip in the y-z cross-section plane (radians)."""
    i, j = strip.connectivity
    yi, zi = ps.node_coords[i]
    yj, zj = ps.node_coords[j]
    return math.atan2(zj - zi, yj - yi)


def _rotation_matrix_8x8(beta: float) -> np.ndarray:
    """Build 8x8 rotation T from strip-local to global DOFs.

    DOF order per node: [u, v, w, theta].
    * u  -- longitudinal (x, along member axis): no rotation needed.
    * v  -- in-plane tangent to strip in cross-section plane: rotated.
    * w  -- out-of-plane normal to strip: rotated.
    * theta -- rotation about strip longitudinal axis: rotated.

    The in-plane / out-of-plane rotation acts on v and w as a 2D rotation
    by angle beta, and on theta similarly.
    """
    c = math.cos(beta)
    s = math.sin(beta)

    # 4x4 block for one node: maps (u_loc, v_loc, w_loc, theta_loc)
    # to (u_glob, v_y, v_z, theta_glob).
    # u is along the member axis -- invariant.
    # v_loc -> v_y =  c*v_loc - s*w_loc
    # w_loc -> v_z =  s*v_loc + c*w_loc
    # theta_loc rotates identically to w.
    R4 = np.array([
        [1.0, 0.0,  0.0, 0.0],
        [0.0,   c,   -s, 0.0],
        [0.0,   s,    c, 0.0],
        [0.0, 0.0,  0.0, 1.0],
    ])

    T = np.zeros((8, 8))
    T[:4, :4] = R4
    T[4:, 4:] = R4
    return T


# ======================================================================
# Membrane stiffness (plane-stress strip, linear shape functions)
# ======================================================================

def _membrane_ke_4x4(width: float, thickness: float, length: float,
                      E: float, nu: float) -> np.ndarray:
    """4x4 membrane elastic stiffness for DOFs (u_i, v_i, u_j, v_j).

    Plane-stress strip with sinusoidal longitudinal mode m=1 and linear
    transverse shape functions.  Formulation from Cheung (1976) / CUFSM.

    The factor (a/2) = L/2 from integration is omitted (cancels in the
    eigenvalue ratio).
    """
    b = width
    t = thickness
    L = length
    p = math.pi / L
    E_star = E / (1.0 - nu ** 2)

    # In-plane terms (Cheung 1976, Table 3.2 simplified for m=1)
    k11 = E_star * t * (p ** 2 * b / 3.0 + 1.0 / b)
    k12 = E_star * t * (nu * p / 2.0 - p / 2.0)  # coupling u-v (antisym)
    k13 = E_star * t * (p ** 2 * b / 6.0 - 1.0 / b)
    k14 = E_star * t * (nu * p / 2.0 + p / 2.0)
    # k22: axial + shear contributions (Cheung 1976)
    k22 = E_star * t * (1.0 / b + (1.0 - nu) / 2.0 * p ** 2 * b / 3.0)
    k24 = E_star * t * (-1.0 / b + (1.0 - nu) / 2.0 * p ** 2 * b / 6.0)

    # Symmetric membrane stiffness
    Km = np.array([
        [ k11,  k12,  k13,  k14],
        [ k12,  k22, -k14,  k24],
        [ k13, -k14,  k11, -k12],
        [ k14,  k24, -k12,  k22],
    ])
    return Km


def _membrane_kg_4x4(
    width: float = 0.0,
    thickness: float = 0.0,
    length: float = 1.0,
    sigma_x: float = 0.0,
    include_membrane_kg: bool = False,
) -> np.ndarray:
    """Geometric stiffness for membrane DOFs (u_i, v_i, u_j, v_j).

    When ``include_membrane_kg=True``, returns the consistent Cheung (1976) /
    CUFSM membrane geometric stiffness matrix:
    ``sigma_x * t * (pi / L)^2 * (b / 6) * [[2,0,1,0],[0,2,0,1],[1,0,2,0],[0,1,0,2]]``.
    """
    if not include_membrane_kg or width <= 0.0 or thickness <= 0.0 or sigma_x == 0.0:
        return np.zeros((4, 4))
    p2 = (math.pi / length) ** 2
    coeff = sigma_x * thickness * p2 * (width / 6.0)
    return coeff * np.array([
        [2.0, 0.0, 1.0, 0.0],
        [0.0, 2.0, 0.0, 1.0],
        [1.0, 0.0, 2.0, 0.0],
        [0.0, 1.0, 0.0, 2.0],
    ])


# ======================================================================
# Coupling between bending and membrane (simplified)
# ======================================================================

def _coupling_blocks(width: float, thickness: float, length: float,
                     E: float, nu: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (K_bm, K_mb) coupling blocks (4x4 each).

    For thin plates the bending-membrane coupling vanishes for flat strips
    (no initial curvature).  We return zeros -- coupling only arises at the
    global assembly level through shared nodal DOFs.
    """
    return np.zeros((4, 4)), np.zeros((4, 4))


# ======================================================================
# Full 8x8 strip stiffness in GLOBAL DOFs
# ======================================================================

def _strip_matrices_global(
    strip: StripDefinition,
    ps: ProfileStrips,
    half_wavelength: float,
    sigma_x: float,
    include_membrane_kg: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Build 8x8 K_E and K_G for one strip in global coordinates.

    DOF order per node: [u, v, w, theta] (4 DOFs x 2 nodes = 8).
    Local order:
        bending block [w_i, theta_i, w_j, theta_j] -> rows/cols 0-3
        membrane block [u_i, v_i, u_j, v_j]        -> rows/cols 4-7

    After assembly in local coords, rotate by strip angle beta.
    """
    b = strip.width_mm
    t = strip.thickness_mm
    E = strip.E_MPa
    nu = strip.nu
    L = half_wavelength

    # -- Bending 4x4 (from JIT kernel) --
    ke_bend, kg_bend = fsm_local_stiffness_matrices_jit(b, t, L, E, nu, sigma_x)

    # -- Membrane 4x4 --
    ke_memb = _membrane_ke_4x4(b, t, L, E, nu)
    kg_memb = _membrane_kg_4x4(b, t, L, sigma_x, include_membrane_kg=include_membrane_kg)

    # Assemble local 8x8.
    # DOF mapping: [u_i, v_i, w_i, theta_i, u_j, v_j, w_j, theta_j]
    # Bending DOFs in JIT: [w_i, theta_i, w_j, theta_j] -> indices [2,3,6,7]
    # Membrane DOFs:       [u_i, v_i, u_j, v_j]         -> indices [0,1,4,5]
    ke_local = np.zeros((8, 8))
    kg_local = np.zeros((8, 8))

    bend_idx = [2, 3, 6, 7]
    memb_idx = [0, 1, 4, 5]

    for r_loc, r_glob in enumerate(bend_idx):
        for c_loc, c_glob in enumerate(bend_idx):
            ke_local[r_glob, c_glob] = ke_bend[r_loc, c_loc]
            kg_local[r_glob, c_glob] = kg_bend[r_loc, c_loc]

    for r_loc, r_glob in enumerate(memb_idx):
        for c_loc, c_glob in enumerate(memb_idx):
            ke_local[r_glob, c_glob] = ke_memb[r_loc, c_loc]
            kg_local[r_glob, c_glob] = kg_memb[r_loc, c_loc]

    # -- Rotation to global --
    beta = _strip_angle(ps, strip)
    T = _rotation_matrix_8x8(beta)
    ke_global = T.T @ ke_local @ T
    kg_global = T.T @ kg_local @ T

    return ke_global, kg_global


# ======================================================================
# Global assembly
# ======================================================================

def assemble_K_E(
    strips: ProfileStrips,
    half_wavelength: float,
    sigma_x_ref: float = 1.0,
) -> np.ndarray:
    """Assemble the global elastic stiffness matrix.

    Parameters
    ----------
    strips : ProfileStrips
        Profile discretisation.
    half_wavelength : float
        Half-wavelength of the longitudinal buckling mode (mm).
    sigma_x_ref : float
        Reference stress only used internally for matrix generation
        (the bending K_E does not depend on stress, but the JIT function
        requires it; only K_G uses it).

    Returns
    -------
    np.ndarray
        Global elastic stiffness matrix (n_dof x n_dof).
    """
    n = strips.n_dof
    K_E = np.zeros((n, n))

    for strip in strips.strips:
        ke_g, _ = _strip_matrices_global(strip, strips, half_wavelength, sigma_x_ref)
        _scatter(K_E, ke_g, strip.connectivity)

    # Enforce symmetry (numerical round-off)
    K_E = 0.5 * (K_E + K_E.T)
    return K_E


def assemble_K_G(
    strips: ProfileStrips,
    half_wavelength: float,
    stress_dist: np.ndarray,
    include_membrane_kg: bool = False,
) -> np.ndarray:
    """Assemble the global geometric stiffness matrix.

    Parameters
    ----------
    strips : ProfileStrips
        Profile discretisation.
    half_wavelength : float
        Half-wavelength (mm).
    stress_dist : np.ndarray
        Vector of edge stresses per strip (length = n_strips).
        Compression positive.
    include_membrane_kg : bool
        If True, includes the consistent membrane geometric stiffness block
        for (u, v) DOFs in addition to the plate-bending Hermite block.

    Returns
    -------
    np.ndarray
        Global geometric stiffness matrix (n_dof x n_dof).
    """
    if len(stress_dist) != strips.n_strips:
        raise ValueError(
            f"stress_dist length ({len(stress_dist)}) != n_strips ({strips.n_strips})"
        )
    n = strips.n_dof
    K_G = np.zeros((n, n))

    for idx, strip in enumerate(strips.strips):
        _, kg_g = _strip_matrices_global(
            strip,
            strips,
            half_wavelength,
            float(stress_dist[idx]),
            include_membrane_kg=include_membrane_kg,
        )
        _scatter(K_G, kg_g, strip.connectivity)

    K_G = 0.5 * (K_G + K_G.T)
    return K_G


def _scatter(K_global: np.ndarray, K_strip: np.ndarray,
             connectivity: tuple[int, int]) -> None:
    """Scatter an 8x8 strip matrix into the global matrix."""
    dofs_per_node = 4
    i, j = connectivity
    # Map: strip DOF 0..3 -> global node i DOFs, strip DOF 4..7 -> global node j DOFs
    global_dofs = []
    for node in (i, j):
        base = node * dofs_per_node
        global_dofs.extend(range(base, base + dofs_per_node))

    for r_loc, r_glob in enumerate(global_dofs):
        for c_loc, c_glob in enumerate(global_dofs):
            K_global[r_glob, c_glob] += K_strip[r_loc, c_loc]


# ======================================================================
# Eigenvalue solver
# ======================================================================

def solve_buckling(
    K_E: np.ndarray,
    K_G: np.ndarray,
    n_modes: int = 5,
    constrained_dofs: list[int] | np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Solve the generalised eigenvalue problem K_E * phi = lambda * K_G * phi.

    Uses ``scipy.linalg.eig`` (not eigh) because K_G may be positive
    semi-definite or indefinite.

    Parameters
    ----------
    K_E : np.ndarray
        Global elastic stiffness matrix.
    K_G : np.ndarray
        Global geometric stiffness matrix.
    n_modes : int
        Number of lowest positive eigenvalues to return.
    constrained_dofs : list[int] or np.ndarray or None
        DOF indices to constrain (set to zero displacement).  The
        corresponding rows/columns are removed before solving.

    Returns
    -------
    eigenvalues : np.ndarray
        Sorted ascending array of the first *n_modes* positive real
        eigenvalues (load factors).
    eigenvectors : np.ndarray
        Corresponding eigenvectors as columns (shape n_free x n_modes
        if constrained_dofs is given, else n_dof x n_modes).
    """
    if K_E.shape != K_G.shape or K_E.ndim != 2:
        raise ValueError("K_E and K_G must be square matrices of the same size")

    # Apply boundary conditions by removing constrained DOFs
    if constrained_dofs is not None and len(constrained_dofs) > 0:
        all_dofs = np.arange(K_E.shape[0])
        free_dofs = np.setdiff1d(all_dofs, constrained_dofs)
        K_E_r = K_E[np.ix_(free_dofs, free_dofs)]
        K_G_r = K_G[np.ix_(free_dofs, free_dofs)]
    else:
        K_E_r = K_E
        K_G_r = K_G

    w, v = eig(K_E_r, K_G_r)

    # Filter: finite, real-dominant, positive
    w_real = w.real
    w_imag = w.imag
    mask = (
        np.isfinite(w_real) &
        (w_real > 1e-6) &
        (np.abs(w_imag) < 1e-6 * np.abs(w_real + 1e-30))
    )

    if not np.any(mask):
        raise RuntimeError("No positive finite eigenvalue found")

    indices = np.where(mask)[0]
    vals = w_real[indices]
    order = np.argsort(vals)
    n_out = min(n_modes, len(order))

    sorted_indices = indices[order[:n_out]]
    eigenvalues = w_real[sorted_indices]
    eigenvectors = v[:, sorted_indices].real

    return eigenvalues, eigenvectors


# ======================================================================
# Signature curve (full FSM)
# ======================================================================

def compute_signature_curve_fsm(
    strips: ProfileStrips,
    stress_dist: np.ndarray,
    half_wavelengths: np.ndarray | None = None,
) -> SignatureResult:
    """Compute the full FSM signature curve sigma_cr vs half-wavelength.

    Parameters
    ----------
    strips : ProfileStrips
        Profile discretisation.
    stress_dist : np.ndarray
        Edge stress per strip (compression positive).
    half_wavelengths : np.ndarray or None
        Array of half-wavelengths to evaluate.  If None, a default
        logarithmic range from 10 mm to 10 000 mm (80 points) is used.

    Returns
    -------
    SignatureResult
        With fields ``half_wavelengths_mm``, ``sigma_cr_MPa``, ``minima``.
    """
    if half_wavelengths is None:
        lams = np.logspace(np.log10(10.0), np.log10(10_000.0), 80)
    else:
        lams = np.asarray(half_wavelengths, dtype=float)

    sigma_cr = np.full_like(lams, np.inf)

    for idx, L in enumerate(lams):
        try:
            K_E = assemble_K_E(strips, L)
            K_G = assemble_K_G(strips, L, stress_dist)
            eigenvalues, _ = solve_buckling(K_E, K_G, n_modes=1)
            sigma_cr[idx] = eigenvalues[0]
        except RuntimeError:
            sigma_cr[idx] = np.inf

    # Scale: the eigenvalue is a load factor on stress_dist.  The critical
    # stress is lambda * sigma_ref where sigma_ref = max(|stress_dist|).
    sigma_ref = float(np.max(np.abs(stress_dist)))
    if sigma_ref > 0:
        sigma_cr_MPa = sigma_cr * sigma_ref
    else:
        sigma_cr_MPa = sigma_cr

    minima = _detect_minima(lams, sigma_cr_MPa)

    return SignatureResult(
        half_wavelengths_mm=lams,
        sigma_cr_MPa=sigma_cr_MPa,
        minima=minima,
    )


def _detect_minima(
    lams: np.ndarray,
    sigma: np.ndarray,
) -> list[tuple[float, float, str]]:
    """Detect local, distortional, and global minima in the signature curve.

    Heuristic based on half-wavelength ranges and local-minimum detection.
    """
    minima: list[tuple[float, float, str]] = []
    finite_mask = np.isfinite(sigma)
    if not np.any(finite_mask):
        return minima

    # Find all local minima (points lower than both neighbours)
    local_min_indices: list[int] = []
    for i in range(1, len(sigma) - 1):
        if finite_mask[i] and sigma[i] < sigma[i - 1] and sigma[i] < sigma[i + 1]:
            local_min_indices.append(i)

    # Also check endpoints if they are finite
    if finite_mask[0] and (len(sigma) < 2 or sigma[0] < sigma[1]):
        local_min_indices.insert(0, 0)
    if finite_mask[-1] and (len(sigma) < 2 or sigma[-1] < sigma[-2]):
        local_min_indices.append(len(sigma) - 1)

    if not local_min_indices:
        # Fallback: just the global minimum
        valid = np.where(finite_mask)[0]
        idx_min = valid[int(np.argmin(sigma[valid]))]
        minima.append((float(lams[idx_min]), float(sigma[idx_min]), "Local"))
        return minima

    # Classify by half-wavelength range
    # Local mode: shortest wavelength minimum (typically lambda ~ b of strip)
    # Distortional: intermediate
    # Global: longest wavelength minimum
    if len(local_min_indices) == 1:
        idx = local_min_indices[0]
        minima.append((float(lams[idx]), float(sigma[idx]), "Local"))
    elif len(local_min_indices) == 2:
        idx0 = local_min_indices[0]
        idx1 = local_min_indices[1]
        minima.append((float(lams[idx0]), float(sigma[idx0]), "Local"))
        minima.append((float(lams[idx1]), float(sigma[idx1]), "Distortional"))
    else:
        idx0 = local_min_indices[0]
        minima.append((float(lams[idx0]), float(sigma[idx0]), "Local"))
        for mid_idx in local_min_indices[1:-1]:
            minima.append((float(lams[mid_idx]), float(sigma[mid_idx]), "Distortional"))
        idx_last = local_min_indices[-1]
        minima.append((float(lams[idx_last]), float(sigma[idx_last]), "Global"))

    return minima


# ======================================================================
# Public API
# ======================================================================

__all__ = [
    "StripDefinition",
    "ProfileStrips",
    "build_profile_strips",
    "assemble_K_E",
    "assemble_K_G",
    "solve_buckling",
    "compute_signature_curve_fsm",
]
