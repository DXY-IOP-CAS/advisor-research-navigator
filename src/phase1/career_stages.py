#!/usr/bin/env python3
"""Shared helpers for career_stages.json handling."""

from typing import Any, Optional


def normalize_stage_config(raw: Any) -> Optional[list]:
    """Return a stage list from either supported career_stages schema.

    Canonical format is a top-level list. Dict-wrapped {"stages": [...]} is
    accepted for compatibility because older guidance and agent outputs used it.
    """
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("stages"), list):
        return raw["stages"]
    return None
