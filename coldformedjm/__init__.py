"""
ColdFormedJm - Thin-walled and Class 4 steel section evaluator.
"""

__version__ = "1.0.0"

try:
    from .sectprops_wrapper import (
        SectionProperties,
        analyze_i_section, analyze_channel_section, analyze_hollow_rect_section,
    )
except ImportError:
    pass  # sectionproperties opcional

from .fsm_jit import fsm_local_stiffness_matrices_jit

__all__ = [
    "SectionProperties",
    "analyze_i_section",
    "analyze_channel_section",
    "analyze_hollow_rect_section",
    "fsm_local_stiffness_matrices_jit",
]
