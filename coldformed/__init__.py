"""
ColdFormed - Thin-walled and Class 4 steel section evaluator.
"""

__version__ = "1.1.0"

_SECTPROPS_ATTRS = {
    "SectionProperties",
    "analyze_i_section",
    "analyze_channel_section",
    "analyze_hollow_rect_section",
}


def __getattr__(name: str):
    if name in _SECTPROPS_ATTRS:
        try:
            from . import sectprops_wrapper
            return getattr(sectprops_wrapper, name)
        except ImportError:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if name == "fsm_local_stiffness_matrices_jit":
        from .fsm_jit import fsm_local_stiffness_matrices_jit
        return fsm_local_stiffness_matrices_jit
    if name in (
        "SectionGeometryCZ",
        "DistortionalResultAISI",
        "DistortionalResultEC3",
        "aisi_distortional_buckling",
        "ec3_distortional_buckling",
    ):
        from . import distortional
        return getattr(distortional, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SectionProperties",
    "analyze_i_section",
    "analyze_channel_section",
    "analyze_hollow_rect_section",
    "fsm_local_stiffness_matrices_jit",
    "SectionGeometryCZ",
    "DistortionalResultAISI",
    "DistortionalResultEC3",
    "aisi_distortional_buckling",
    "ec3_distortional_buckling",
]

