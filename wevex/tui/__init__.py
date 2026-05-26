"""Wevex TUI — Textual-based control panel.

Single entry point: ``WevexApp``. Launched by ``wevex tui`` (see cli.py).
"""
from __future__ import annotations

from .app import WevexApp

__all__ = ["WevexApp"]
