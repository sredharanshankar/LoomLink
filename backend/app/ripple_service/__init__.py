"""Ripple service DB adapter — owned by Lane B.

Foundation stub: register() is called from main.py lifespan so Lane B can
subscribe domain-event handlers without editing main.py.
"""


def register() -> None:
    """Subscribe the debounced Ripple recompute loop."""
    from .engine_runner import register as register_runner

    register_runner()
