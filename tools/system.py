from __future__ import annotations

import os
import platform
import shutil
import subprocess
from collections.abc import Mapping

import psutil


class SafeAppLauncher:
    """Launches only aliases explicitly configured by the user."""

    def __init__(self, aliases: Mapping[str, str]) -> None:
        self.aliases = {str(k).strip(): str(v).strip() for k, v in aliases.items()}

    def names(self) -> list[str]:
        return sorted(self.aliases)

    def open(self, app: str) -> dict[str, object]:
        target = self.aliases.get(app)
        if target is None:
            lowered = app.casefold().strip()
            for alias, value in self.aliases.items():
                if alias.casefold() == lowered:
                    app, target = alias, value
                    break
        if not target:
            return {"ok": False, "error": f"App alias is not configured: {app}"}

        system = platform.system().lower()
        if system == "windows":
            subprocess.Popen([target], shell=False)
        elif system == "darwin":
            subprocess.Popen(["open", "-a", target])
        else:
            executable = shutil.which(target) or target
            subprocess.Popen([executable])
        return {"ok": True, "app": app}


def system_status() -> dict[str, object]:
    vm = psutil.virtual_memory()
    return {
        "ok": True,
        "os": platform.system(),
        "cpu_percent": psutil.cpu_percent(interval=0.15),
        "memory_percent": vm.percent,
        "memory_available_gb": round(vm.available / 1024**3, 2),
    }
