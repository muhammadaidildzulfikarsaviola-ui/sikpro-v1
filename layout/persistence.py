"""Versioned, atomic Layout project file support."""
import json
import os
from pathlib import Path
import tempfile

from .models import LayoutProject


FORMAT_NAME = "sikpro-layout"
FORMAT_VERSION = 1


def serialize_project(project: LayoutProject) -> dict:
    project.require_valid_inputs(require_complete_relationships=False)
    return {"format": FORMAT_NAME, "version": FORMAT_VERSION, "project": project.to_dict()}


def save_project(path, project: LayoutProject) -> Path:
    target = Path(path)
    payload = json.dumps(serialize_project(project), ensure_ascii=False, indent=2, allow_nan=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def load_project(path) -> LayoutProject:
    with open(path, "r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict) or payload.get("format") != FORMAT_NAME:
        raise ValueError("not a SIKPRO Layout project file")
    if payload.get("version") != FORMAT_VERSION:
        raise ValueError(f"unsupported Layout project version: {payload.get('version')}")
    if not isinstance(payload.get("project"), dict):
        raise ValueError("project data must be an object")
    return LayoutProject.from_dict(payload["project"])
