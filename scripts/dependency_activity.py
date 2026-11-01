"""Single dependency lifecycle owner; numeric positions use half-open intervals."""
import json
import math
from typing import Any


def is_edge_active(edge: dict[str, Any], at: float | None = None, policy: str = "active_at") -> bool:
    if policy == "historical_all":
        return True
    if policy != "active_at":
        raise ValueError(f"unsupported dependency activity policy: {policy}")
    status = str(edge.get("status", "active"))
    if at is None:
        return status == "active"
    if hasattr(at, "axis"):
        if at.axis != edge.get("axis", "revision") or at.domain != edge.get("domain", "sequence"):
            return False
        at = at.value
    elif edge.get("axis", "revision") != "revision" or edge.get("domain", "sequence") != "sequence":
        # Legacy numeric arguments explicitly mean revision sequence.
        return False
    if not isinstance(at, (int, float)) or not math.isfinite(at):
        return False
    start = edge.get("valid_from")
    end = edge.get("valid_until", edge.get("valid_to", edge.get("retired_at")))
    # Retired history is available only with explicit bounds; otherwise closed.
    if status != "active" and not (status in {"retired", "superseded", "invalidated"} and start is not None and end is not None):
        return False
    try:
        if start is not None and (not math.isfinite(float(start)) or at < float(start)):
            return False
        if end is not None and (not math.isfinite(float(end)) or at >= float(end)):
            return False
    except (TypeError, ValueError):
        return False
    return True


def active_edges(rows: list[dict[str, Any]], at: float | None = None, policy: str = "active_at") -> list[dict[str, Any]]:
    return sorted((e for e in rows if is_edge_active(e, at, policy)), key=lambda e: json.dumps(e, sort_keys=True, ensure_ascii=False))
