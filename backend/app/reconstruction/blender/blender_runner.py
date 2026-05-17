"""Headless Blender execution helpers for worker processes."""

from __future__ import annotations

import shlex


class BlenderRunner:
    """Construct safe headless commands for Blender automation."""

    def build_command(self, script_path: str, args: list[str] | None = None) -> str:
        base = ["blender", "--background", "--python", script_path]
        if args:
            base.extend(["--", *args])
        return " ".join(shlex.quote(part) for part in base)
