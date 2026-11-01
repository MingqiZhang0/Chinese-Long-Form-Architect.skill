#!/usr/bin/env python3
"""Create a deterministic paragraph-alignment and revision-routing manifest.

This script reports where prose changed and routes externally declared Project-Poetics
changes into their own classification/invalidation-review path. It never infers canon
or literary impact from surface statistics.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from narrative_runtime import dependency_rows, impact
from dependency_activity import is_edge_active
from prose_state_reconcile import safe_path, anchor, verify_anchor


def dependency_packet(root: Path, dependencies: Path, seeds: list[str],
                      chapters_dir: str, branch: str) -> dict[str, Any]:
    """Retrieve graph witnesses AND all supplied chapter prose; never infer damage."""
    source = safe_path(root, str(dependencies))
    raw = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and raw.get("branch", branch) != branch:
        raise ValueError("dependency graph belongs to a different branch")
    edges = [row for row in dependency_rows(raw)
             if row.get("branch", branch) == branch and is_edge_active(row)]
    targets: dict[str, list[dict[str, Any]]] = {}
    reached = set(seeds)
    for seed in seeds:
        rows = impact(edges, seed)
        for row in rows:
            targets.setdefault(row["target"], []).append({"seed": seed, **row})
            reached.add(row["target"])
    chapters = safe_path(root, chapters_dir)
    if not chapters.is_dir():
        raise ValueError("chapter scan directory is missing")
    items = [{"review_id": "node:" + node, "kind": "dependency_node", "node": node,
              "graph_witnesses": witnesses,
              # Preserve alternative supports, including those outside the changed closure.
              "upstream_edges": [edge for edge in edges if str(edge.get("target")) == node]}
             for node, witnesses in sorted(targets.items())]
    inventory = []
    for path in sorted(chapters.rglob("*.md")):
        path = safe_path(root, str(path))
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        ev = [anchor(root, path, 1, len(lines))] if lines else []
        inventory.append({"path": rel, "sha256": sha256(path)})
        items.append({"review_id": "chapter:" + rel, "kind": "chapter_scan",
                      "evidence": ev, "text": "\n".join(lines)})
    if not inventory:
        raise ValueError("chapter scan contains no Markdown prose")
    return {"packet_version": "1.0.0", "branch": branch, "changed_nodes": seeds,
            "dependencies": {"path": source.relative_to(root).as_posix(), "sha256": sha256(source)},
            "chapters_dir": chapters_dir, "chapter_inventory": inventory,
            "review_items": items, "status": "PENDING_REVIEW",
            "note": "Reachability is a review candidate, not invalidation. Read every chapter to discover unindexed dependencies; inspect alternative supports. No semantic completeness claim."}


def validate_dependency_review(report: dict[str, Any], root: Path) -> list[str]:
    """Check approved semantic decisions against a fresh, exhaustive retrieval packet."""
    review = report.get("dependency_review")
    if review is None:
        return []  # Legacy reports remain supported without claiming discovery coverage.
    errors: list[str] = []
    try:
        from runtime_schema import validate_instance
        errors = validate_instance(report, Path(__file__).resolve().parents[1] / "assets/runtime-schemas/revision-impact.schema.json")
        if errors:
            return errors
        packet_path = safe_path(root, review["packet_path"])
        if sha256(packet_path) != review["packet_sha256"]:
            return ["dependency review packet is stale"]
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        if packet["branch"] != report["branch"]:
            errors.append("dependency review branch mismatch")
        current = dependency_packet(root, Path(packet["dependencies"]["path"]),
                                    packet["changed_nodes"], packet["chapters_dir"], packet["branch"])
        if current != {key: value for key, value in packet.items() if key != "revision_sources"}:
            errors.append("dependency retrieval inputs or chapter inventory changed; rebuild review")
        sources = packet.get("revision_sources", [])
        if len(sources) != 2:
            errors.append("dependency packet must bind before/after revision sources")
        else:
            for item, key in zip(sources, ("before_hash", "after_hash")):
                if sha256(safe_path(root, item["path"])) != item["sha256"] or report[key] != item["sha256"]:
                    errors.append(f"dependency review {key} source is stale or belongs to another revision")
        expected = {row["review_id"] for row in packet["review_items"]}
        decisions = review["decisions"]
        ids = [row["review_id"] for row in decisions]
        approved = report["approval_status"] in {"PROSE_ONLY_CONFIRMED", "APPROVED_FOR_COMMIT"}
        if len(ids) != len(set(ids)) or not set(ids) <= expected or (approved and set(ids) != expected):
            errors.append("dependency decisions must cover graph targets and every scanned chapter exactly once")
        for row in decisions:
            if approved and (row["status"] == "unresolved" or not row["rationale"].strip()):
                errors.append(f"unresolved dependency decision: {row['review_id']}")
            if row["status"] == "affected":
                if not row["evidence"] or not row["repairs"]:
                    errors.append(f"affected dependency needs evidence and repair alternatives: {row['review_id']}")
                if report["approval_status"] == "PROSE_ONLY_CONFIRMED":
                    errors.append("PROSE_ONLY_CONFIRMED cannot carry affected downstream premises")
            for ev in row["evidence"]:
                errors.extend(verify_anchor(ev, root))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"invalid dependency review: {exc}")
    return errors


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def paragraphs(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", x.strip()) for x in re.split(r"\n\s*\n", text) if x.strip()]


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def align(before: list[str], after: list[str]) -> list[dict[str, Any]]:
    sm = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    out: list[dict[str, Any]] = []
    counter = 1
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for off in range(i2 - i1):
                out.append({
                    "alignment_id": f"A-{counter:04d}", "status": "unchanged",
                    "before_index": i1 + off, "after_index": j1 + off,
                    "similarity": 1.0,
                })
                counter += 1
            continue
        if tag == "delete":
            for i in range(i1, i2):
                out.append({"alignment_id": f"A-{counter:04d}", "status": "deleted", "before_index": i, "after_index": None, "similarity": 0.0})
                counter += 1
            continue
        if tag == "insert":
            for j in range(j1, j2):
                out.append({"alignment_id": f"A-{counter:04d}", "status": "inserted", "before_index": None, "after_index": j, "similarity": 0.0})
                counter += 1
            continue

        left = list(range(i1, i2))
        right = list(range(j1, j2))
        pairs: list[tuple[float, int, int]] = []
        for i in left:
            for j in right:
                pairs.append((similarity(before[i], after[j]), i, j))
        used_i: set[int] = set()
        used_j: set[int] = set()
        for score, i, j in sorted(pairs, reverse=True):
            if score < 0.25 or i in used_i or j in used_j:
                continue
            used_i.add(i); used_j.add(j)
            out.append({"alignment_id": f"A-{counter:04d}", "status": "modified", "before_index": i, "after_index": j, "similarity": round(score, 4)})
            counter += 1
        for i in left:
            if i not in used_i:
                out.append({"alignment_id": f"A-{counter:04d}", "status": "deleted", "before_index": i, "after_index": None, "similarity": 0.0})
                counter += 1
        for j in right:
            if j not in used_j:
                out.append({"alignment_id": f"A-{counter:04d}", "status": "inserted", "before_index": None, "after_index": j, "similarity": 0.0})
                counter += 1
    out.sort(key=lambda x: (10**9 if x["after_index"] is None else x["after_index"], 10**9 if x["before_index"] is None else x["before_index"]))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--chapter-id", default="UNKNOWN")
    p.add_argument("--branch", default="main")
    p.add_argument(
        "--poetics-changed", action="store_true",
        help=(
            "record that an approved Project-Poetics change accompanies this revision; "
            "this forces Project-Poetics classification and downstream invalidation review "
            "even when the before/after prose bytes are unchanged"
        ),
    )
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--review-root", type=Path, help="project root for dependency-discovery packet")
    p.add_argument("--dependencies", type=Path, help="existing dependency graph (retrieval only)")
    p.add_argument("--changed-node", action="append", default=[], help="reviewed semantic seed node; repeat for multiple premises")
    p.add_argument("--chapters-dir", default="chapters", help="branch-scoped Markdown prose directory; scanned even without indexed edges")
    p.add_argument("--review-out", type=Path, help="output dependency review packet")
    args = p.parse_args()
    packet = None
    if any([args.review_root, args.dependencies, args.changed_node, args.review_out]):
        if not all([args.review_root, args.dependencies, args.changed_node, args.review_out]):
            p.error("dependency discovery requires --review-root, --dependencies, --changed-node and --review-out")
        try:
            packet = dependency_packet(args.review_root.resolve(), args.dependencies,
                                       args.changed_node, args.chapters_dir, args.branch)
            packet["revision_sources"] = [
                {"path": safe_path(args.review_root.resolve(), str(path.resolve())).relative_to(args.review_root.resolve()).as_posix(),
                 "sha256": sha256(path)} for path in (args.before, args.after)]
        except (OSError, ValueError) as exc:
            p.error(str(exc))
    before_text = args.before.read_text(encoding="utf-8")
    after_text = args.after.read_text(encoding="utf-8")
    bp = paragraphs(before_text)
    ap = paragraphs(after_text)
    rows = align(bp, ap)
    changed = [x for x in rows if x["status"] != "unchanged"]
    text_change_detected = bool(changed)
    poetics_change_declared = bool(args.poetics_changed)

    classification_axes: list[str] = []
    if text_change_detected:
        classification_axes.append("diegetic_semantics")
    if poetics_change_declared:
        classification_axes.append("project_poetics")

    if text_change_detected and poetics_change_declared:
        revision_kind = "prose_and_poetics"
    elif text_change_detected:
        revision_kind = "prose"
    elif poetics_change_declared:
        revision_kind = "poetics_only"
    else:
        revision_kind = "no_change"

    poetics_invalidation_review_domains = (
        [
            "narrative_strategy",
            "chapter_and_writer_missions",
            "compiled_context_packs",
            "style_and_voice_diagnostics",
        ]
        if poetics_change_declared
        else []
    )

    result = {
        "schema_version": "1.1.0",
        "chapter_id": args.chapter_id,
        "branch": args.branch,
        "before_path": str(args.before),
        "after_path": str(args.after),
        "before_hash": sha256(args.before),
        "after_hash": sha256(args.after),
        "before_paragraphs": len(bp),
        "after_paragraphs": len(ap),
        "alignments": rows,
        "changed_alignment_ids": [x["alignment_id"] for x in changed],
        "revision_kind": revision_kind,
        "text_change_detected": text_change_detected,
        "poetics_change_declared": poetics_change_declared,
        "diegetic_classification_required": text_change_detected,
        "poetics_classification_required": poetics_change_declared,
        "semantic_classification_required": text_change_detected or poetics_change_declared,
        "classification_axes": classification_axes,
        "poetics_invalidation_review_required": poetics_change_declared,
        "poetics_invalidation_review_domains": poetics_invalidation_review_domains,
        "note": (
            "Mechanical alignment and workflow routing only; neither canon impact nor Project-Poetics impact is inferred. "
            "semantic_classification_required is a backward-compatible aggregate gate; consumers should prefer the "
            "axis-specific diegetic_classification_required and poetics_classification_required fields. "
            "When --poetics-changed is declared, poetics_invalidation_review_domains are review domains, not automatic stale marks: "
            "invalidate only the affected dependency closure after Project-Poetics impact classification."
        ),
    }
    if packet is not None:
        output = safe_path(args.review_root.resolve(), str(args.review_out.resolve()))
        if output.exists():
            p.error("refusing to overwrite an existing dependency packet")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["dependency_review_packet"] = {"path": output.relative_to(args.review_root.resolve()).as_posix(), "sha256": sha256(output)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"aligned {len(rows)} paragraph records; {len(changed)} changed; revision_kind={revision_kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
