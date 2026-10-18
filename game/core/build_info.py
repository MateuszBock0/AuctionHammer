"""Provenance of the exact code bundled with a match audit.

Windows CI writes data/BUILD_INFO.json immediately before the PyInstaller
build. Never guess a release commit from the currently installed launcher.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

_COMMIT_RE=re.compile(r"^[0-9a-f]{40}$")


def _roots():
    if getattr(sys,"frozen",False) and hasattr(sys,"_MEIPASS"):
        yield Path(sys._MEIPASS)
    yield Path(__file__).resolve().parents[2]


def build_identity():
    """Return verifiable commit provenance, or explicitly UNKNOWN."""
    for root in _roots():
        stamp=root/"data"/"BUILD_INFO.json"
        if not stamp.is_file():
            continue
        try:
            data=json.loads(stamp.read_text(encoding="utf-8"))
            commit=str(data["commit"]).lower()
            if _COMMIT_RE.fullmatch(commit):
                return {"commit":commit,"source":"embedded-ci",
                        "version":str(data.get("version","unknown"))}
        except (OSError,ValueError,KeyError,TypeError):
            pass
    # Source checkouts: report HEAD only for local developer sessions.
    if not getattr(sys,"frozen",False):
        root=Path(__file__).resolve().parents[2]
        if (root/".git").exists():
            try:
                result=subprocess.run(["git","rev-parse","HEAD"],
                                      cwd=root,timeout=3,capture_output=True,
                                      text=True,check=True)
                sha=result.stdout.strip().lower()
                if _COMMIT_RE.fullmatch(sha):
                    return {"commit":sha,"source":"source-checkout",
                            "version":"unknown"}
            except (OSError,subprocess.SubprocessError):
                pass
    return {"commit":None,"source":"unknown","version":"unknown"}
