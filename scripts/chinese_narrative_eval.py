#!/usr/bin/env python3
"""Deterministic tooling for Chinese Narrative Behavioral Evaluation.

This module validates corpus contracts, builds blind packets, scores categorical
responses, and aggregates human annotations. It is infrastructure, not a
literary judge, and it deliberately avoids producing a universal prose-quality
score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets/chinese-narrative-eval"
DEFAULT_CORPUS = ASSET_DIR / "seed-families.jsonl"
TAXONOMY_PATH = ASSET_DIR / "taxonomy.json"
GLOBAL_RESEARCH_LEDGER = ROOT / "assets/external-research-ledger.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{lineno}: each JSONL record must be an object")
            value["__line__"] = lineno
            records.append(value)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def clean_internal(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if not k.startswith("__")}


def taxonomy() -> dict[str, Any]:
    return load_json(TAXONOMY_PATH)


def _item_id(family_id: str, variant_id: str) -> str:
    return f"{family_id}::{variant_id}"


def _validate_packaged_manifest(path: Path, summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if path.resolve() != DEFAULT_CORPUS.resolve():
        return errors
    manifest_path = ASSET_DIR / "corpus-manifest.json"
    research_path = ASSET_DIR / "research-ledger.json"
    if not manifest_path.is_file():
        return ["packaged Chinese evaluation corpus is missing corpus-manifest.json"]
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        return [f"invalid corpus-manifest.json: {exc}"]
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if manifest.get("seed_sha256") != actual_hash:
        errors.append("seed-families.jsonl SHA-256 does not match corpus-manifest.json")
    if manifest.get("family_count") != summary.get("families"):
        errors.append("corpus-manifest family_count drifted from seed corpus")
    if manifest.get("variant_count") != summary.get("variants"):
        errors.append("corpus-manifest variant_count drifted from seed corpus")
    if manifest.get("private_holdout_packaged") is not False:
        errors.append("corpus-manifest must state private_holdout_packaged=false")
    if not research_path.is_file():
        errors.append("packaged Chinese evaluation corpus is missing research-ledger.json view")
    elif not GLOBAL_RESEARCH_LEDGER.is_file():
        errors.append("packaged Skill is missing assets/external-research-ledger.json")
    else:
        try:
            view = load_json(research_path)
            ledger = load_json(GLOBAL_RESEARCH_LEDGER)
            if view.get("canonical_ledger") != "assets/external-research-ledger.json":
                errors.append("Chinese evaluation research view points to the wrong canonical ledger")
            source_ids = view.get("source_ids")
            if not isinstance(source_ids, list) or not source_ids:
                errors.append("Chinese evaluation research view has no source_ids")
            else:
                known = {row.get("id") for row in ledger.get("sources", []) if isinstance(row, dict)}
                unknown = sorted(str(x) for x in source_ids if x not in known)
                if unknown:
                    errors.append("Chinese evaluation research view references unknown source ids: " + ", ".join(unknown))
        except Exception as exc:
            errors.append(f"invalid Chinese evaluation research view/canonical ledger: {exc}")
    return errors


def validate_corpus(path: Path, *, allow_private_holdout: bool = False) -> tuple[list[str], list[str], dict[str, Any]]:
    tax = taxonomy()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        families = load_jsonl(path)
    except Exception as exc:
        return [str(exc)], warnings, {"families": 0, "variants": 0}

    ids: set[str] = set()
    variant_count = 0
    role_counts: Counter[str] = Counter()
    phenomenon_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()

    allowed_scope = set(tax["scopes"])
    allowed_dims = set(tax["judgment_dimensions"])
    allowed_evidence = set(tax["evidence_classes"])
    allowed_roles = set(tax["variant_roles"])
    allowed_preferences = set(tax["preferences"])
    allowed_strengths = set(tax["strengths"])
    allowed_provenance = set(tax["provenance_classes"])
    allowed_splits = set(tax["splits"])
    allowed_statuses = set(tax["family_statuses"])
    known_tags = set(tax["phenomenon_tags"])

    required_family = {
        "schema_version", "family_id", "title", "phenomenon_tags", "scope",
        "judgment_dimensions", "split", "family_status", "conditions",
        "invariant_semantics", "provenance", "rights", "variants",
    }

    for family in families:
        line = family.get("__line__", "?")
        prefix = f"{path}:{line}"
        missing = sorted(required_family - set(family))
        if missing:
            errors.append(f"{prefix}: missing family fields: {', '.join(missing)}")
            continue
        family_id = family.get("family_id")
        if not isinstance(family_id, str) or not family_id:
            errors.append(f"{prefix}: family_id must be a non-empty string")
            continue
        if family_id in ids:
            errors.append(f"{prefix}: duplicate family_id {family_id}")
        ids.add(family_id)

        if family.get("schema_version") != "0.1.0":
            errors.append(f"{family_id}: unsupported schema_version {family.get('schema_version')!r}")
        if family.get("scope") not in allowed_scope:
            errors.append(f"{family_id}: invalid scope {family.get('scope')!r}")
        split = family.get("split")
        if split not in allowed_splits:
            errors.append(f"{family_id}: invalid split {split!r}")
        else:
            split_counts[split] += 1
        if split == "private_holdout" and not allow_private_holdout:
            errors.append(f"{family_id}: private_holdout must remain external to the packaged Skill")
        status = family.get("family_status")
        if status not in allowed_statuses:
            errors.append(f"{family_id}: invalid family_status {status!r}")
        else:
            status_counts[status] += 1

        tags = family.get("phenomenon_tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(x, str) and x for x in tags):
            errors.append(f"{family_id}: phenomenon_tags must be a non-empty string list")
            tags = []
        if len(tags) != len(set(tags)):
            errors.append(f"{family_id}: phenomenon_tags contains duplicates")
        for tag in tags:
            phenomenon_counts[tag] += 1
            if tag not in known_tags:
                warnings.append(f"{family_id}: unregistered phenomenon tag {tag!r}; extend taxonomy if intentional")

        dims = family.get("judgment_dimensions")
        if not isinstance(dims, list) or not dims:
            errors.append(f"{family_id}: judgment_dimensions must be non-empty")
            dims = []
        for dim in dims:
            if dim not in allowed_dims:
                errors.append(f"{family_id}: invalid judgment dimension {dim!r}")

        invariants = family.get("invariant_semantics")
        if not isinstance(invariants, list) or not invariants or not all(isinstance(x, str) and x.strip() for x in invariants):
            errors.append(f"{family_id}: invariant_semantics must be a non-empty string list")

        prov = family.get("provenance")
        if not isinstance(prov, dict):
            errors.append(f"{family_id}: provenance must be an object")
        else:
            if prov.get("class") not in allowed_provenance:
                errors.append(f"{family_id}: invalid provenance.class {prov.get('class')!r}")
            if prov.get("source_text_included") is not False and split != "private_holdout":
                errors.append(f"{family_id}: packaged/public corpus must not include external source text")

        rights = family.get("rights")
        if not isinstance(rights, dict):
            errors.append(f"{family_id}: rights must be an object")
        else:
            origin = rights.get("text_origin")
            if origin not in {"original", "licensed"}:
                errors.append(f"{family_id}: rights.text_origin must be original or licensed")
            if rights.get("copied_source_text") is not False and split != "private_holdout":
                errors.append(f"{family_id}: packaged corpus must not contain copied source text")
            if origin == "licensed" and not rights.get("source_license"):
                errors.append(f"{family_id}: licensed text requires rights.source_license")
            if split != "private_holdout" and rights.get("distribution_status") != "packaged":
                errors.append(f"{family_id}: non-private packaged family must declare distribution_status=packaged")
            if split == "private_holdout" and rights.get("distribution_status") != "external_private":
                warnings.append(f"{family_id}: private_holdout should normally declare distribution_status=external_private")

        variants = family.get("variants")
        if not isinstance(variants, list) or len(variants) < 2:
            errors.append(f"{family_id}: contrast family must contain at least two variants")
            continue
        seen_variants: set[str] = set()
        family_roles: Counter[str] = Counter()
        for idx, variant in enumerate(variants, start=1):
            variant_count += 1
            vp = f"{family_id} variant#{idx}"
            if not isinstance(variant, dict):
                errors.append(f"{vp}: variant must be an object")
                continue
            for field in ("variant_id", "role", "context", "candidate_a", "candidate_b", "intended_delta", "gold"):
                if field not in variant:
                    errors.append(f"{vp}: missing {field}")
            vid = variant.get("variant_id")
            if not isinstance(vid, str) or not vid:
                errors.append(f"{vp}: invalid variant_id")
                continue
            if vid in seen_variants:
                errors.append(f"{family_id}: duplicate variant_id {vid}")
            seen_variants.add(vid)
            role = variant.get("role")
            if role not in allowed_roles:
                errors.append(f"{family_id}::{vid}: invalid role {role!r}")
            else:
                family_roles[role] += 1
                role_counts[role] += 1
            for field in ("candidate_a", "candidate_b", "intended_delta"):
                if not isinstance(variant.get(field), str) or not variant.get(field):
                    errors.append(f"{family_id}::{vid}: {field} must be a non-empty string")
            if variant.get("candidate_a") == variant.get("candidate_b"):
                errors.append(f"{family_id}::{vid}: candidates must differ")
            gold = variant.get("gold")
            if not isinstance(gold, dict):
                errors.append(f"{family_id}::{vid}: gold must be an object")
                continue
            pref = gold.get("preference")
            strength = gold.get("strength")
            evidence = gold.get("evidence_class")
            if pref not in allowed_preferences:
                errors.append(f"{family_id}::{vid}: invalid gold.preference {pref!r}")
            if strength not in allowed_strengths:
                errors.append(f"{family_id}::{vid}: invalid gold.strength {strength!r}")
            if evidence not in allowed_evidence:
                errors.append(f"{family_id}::{vid}: invalid gold.evidence_class {evidence!r}")
            if pref in {"tie", "context_dependent"} and strength != "na":
                warnings.append(f"{family_id}::{vid}: non-directional gold should normally use strength=na")
            if not isinstance(gold.get("rationale"), str) or not gold.get("rationale", "").strip():
                errors.append(f"{family_id}::{vid}: gold.rationale must be non-empty")

        if family_roles["anchor"] < 1:
            errors.append(f"{family_id}: family lacks an anchor variant")
        if family_roles["reversal"] + family_roles["boundary"] < 1:
            errors.append(f"{family_id}: family lacks reversal/boundary anti-heuristic coverage")

    summary = {
        "families": len(families),
        "variants": variant_count,
        "splits": dict(sorted(split_counts.items())),
        "statuses": dict(sorted(status_counts.items())),
        "roles": dict(sorted(role_counts.items())),
        "phenomena": dict(sorted(phenomenon_counts.items())),
    }
    errors.extend(_validate_packaged_manifest(path, summary))
    return errors, warnings, summary


def _selected_families(path: Path, splits: set[str], allow_private_holdout: bool) -> list[dict[str, Any]]:
    errors, warnings, _ = validate_corpus(path, allow_private_holdout=allow_private_holdout)
    if errors:
        raise ValueError("corpus validation failed:\n- " + "\n- ".join(errors))
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    return [x for x in load_jsonl(path) if x.get("split") in splits]


def build_blind(
    corpus: Path,
    packet_path: Path,
    key_path: Path,
    *,
    mode: str,
    seed: int,
    splits: set[str],
    allow_private_holdout: bool,
) -> dict[str, Any]:
    if packet_path.resolve() == key_path.resolve():
        raise ValueError("packet and key must be different files")
    families = _selected_families(corpus, splits, allow_private_holdout)
    rng = random.Random(seed)
    packet: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    skipped = 0

    for family in families:
        for variant in family["variants"]:
            gold = variant["gold"]
            canonical_pref = gold["preference"]
            if mode == "repair" and canonical_pref not in {"A", "B"}:
                skipped += 1
                continue
            swapped = bool(rng.getrandbits(1))
            ca = variant["candidate_a"]
            cb = variant["candidate_b"]
            display_a, display_b = (cb, ca) if swapped else (ca, cb)
            map_display_to_canonical = {"A": "B", "B": "A"} if swapped else {"A": "A", "B": "B"}
            if canonical_pref in {"A", "B"}:
                gold_display = "A" if map_display_to_canonical["A"] == canonical_pref else "B"
            else:
                gold_display = canonical_pref
            item_id = _item_id(family["family_id"], variant["variant_id"])

            if mode in {"recognition", "diagnosis"}:
                item = {
                    "schema_version": "0.1.0",
                    "item_id": item_id,
                    "mode": mode,
                    "context": variant.get("context", ""),
                    "candidate_a": display_a,
                    "candidate_b": display_b,
                }
                if mode == "recognition":
                    item["instruction"] = "在给定语境下，仅就当前测试所需的中文叙事适配性判断 A、B，或选择 tie/context_dependent。不要猜测隐藏规则。"
                else:
                    item["instruction"] = "比较 A、B 在该语境中的差异，指出真正起作用的中文叙事机制；不要假设某个表面结构永远更好。"
            elif mode == "repair":
                bad_canonical = "B" if canonical_pref == "A" else "A"
                target = ca if bad_canonical == "A" else cb
                item = {
                    "schema_version": "0.1.0",
                    "item_id": item_id,
                    "mode": mode,
                    "context": variant.get("context", ""),
                    "target_text": target,
                    "instruction": "只修复当前语境中的目标问题，尽量保持原意、人物口吻、视角权限与无关措辞不变。",
                }
            else:
                raise ValueError(f"unsupported blind-packet mode: {mode}")

            packet.append(item)
            key.append({
                "schema_version": "0.1.0",
                "item_id": item_id,
                "family_id": family["family_id"],
                "variant_id": variant["variant_id"],
                "role": variant["role"],
                "scope": family["scope"],
                "phenomenon_tags": family["phenomenon_tags"],
                "judgment_dimensions": family["judgment_dimensions"],
                "family_status": family["family_status"],
                "mode": mode,
                "display_to_canonical": map_display_to_canonical if mode != "repair" else None,
                "gold_canonical": canonical_pref,
                "gold_display": gold_display if mode != "repair" else None,
                "gold_strength": gold["strength"],
                "evidence_class": gold["evidence_class"],
                "rationale": gold["rationale"],
                "intended_delta": variant["intended_delta"],
                "invariant_semantics": family["invariant_semantics"],
            })

    write_jsonl(packet_path, packet)
    write_jsonl(key_path, key)
    return {"items": len(packet), "skipped": skipped, "mode": mode, "seed": seed, "splits": sorted(splits), "packet": str(packet_path), "key": str(key_path)}


def _load_key(path: Path) -> dict[str, dict[str, Any]]:
    records = load_jsonl(path)
    out: dict[str, dict[str, Any]] = {}
    for record in records:
        item_id = record.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"invalid key item_id in {path}:{record.get('__line__')}")
        if item_id in out:
            raise ValueError(f"duplicate key item_id {item_id}")
        out[item_id] = clean_internal(record)
    return out


def score_responses(response_path: Path, key_path: Path) -> dict[str, Any]:
    key = _load_key(key_path)
    responses = load_jsonl(response_path)
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    unknown: list[str] = []

    for response in responses:
        item_id = response.get("item_id")
        choice = response.get("choice")
        if item_id not in key:
            unknown.append(str(item_id))
            continue
        if item_id in seen:
            raise ValueError(f"duplicate response for {item_id}")
        seen.add(item_id)
        if choice not in {"A", "B", "tie", "context_dependent"}:
            raise ValueError(f"{item_id}: choice must be A/B/tie/context_dependent")
        k = key[item_id]
        if k.get("mode") == "repair":
            raise ValueError("repair outputs require human/preservation review; categorical score is not defined")
        gold = k.get("gold_display")
        rows.append({**k, "choice": choice, "correct": choice == gold})

    for item_id in key:
        if item_id not in seen:
            missing.append(item_id)

    def profile(field: str, multi: bool = False) -> dict[str, Any]:
        agg: dict[str, list[bool]] = defaultdict(list)
        for row in rows:
            values = row.get(field, []) if multi else [row.get(field)]
            for value in values:
                agg[str(value)].append(bool(row["correct"]))
        return {
            name: {"n": len(vals), "matches": sum(vals), "rate": round(sum(vals) / len(vals), 6) if vals else None}
            for name, vals in sorted(agg.items())
        }

    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        families[row["family_id"]].append(row)
    family_complete = {
        fid: {
            "n_scored": len(vals),
            "all_scored_correct": all(x["correct"] for x in vals),
            "roles": sorted({x["role"] for x in vals}),
        }
        for fid, vals in sorted(families.items())
    }

    return {
        "evaluated_items": len(rows),
        "categorical_matches": sum(bool(x["correct"]) for x in rows),
        "missing_items": missing,
        "unknown_response_items": unknown,
        "profiles": {
            "phenomenon": profile("phenomenon_tags", multi=True),
            "role": profile("role"),
            "scope": profile("scope"),
            "evidence_class": profile("evidence_class"),
        },
        "family_complete": family_complete,
        "note": "Profile only. Do not interpret categorical agreement as a universal Chinese literary-quality score.",
    }


def _canonical_choice(display_choice: str, key_record: dict[str, Any]) -> str:
    if display_choice in {"tie", "context_dependent"}:
        return display_choice
    mapping = key_record.get("display_to_canonical")
    if not isinstance(mapping, dict):
        raise ValueError(f"{key_record.get('item_id')}: key has no A/B display mapping")
    return mapping[display_choice]


def aggregate_annotations(annotation_path: Path, key_path: Path, *, min_votes: int, consensus: float) -> dict[str, Any]:
    if min_votes < 1:
        raise ValueError("min_votes must be >= 1")
    if not (0.5 <= consensus <= 1.0):
        raise ValueError("consensus must be between 0.5 and 1.0")
    tax = taxonomy()
    allowed_dims = set(tax["judgment_dimensions"])
    allowed_strengths = set(tax["strengths"])
    allowed_flags = {"unclear_context", "both_good", "both_bad", "suspected_confound", "register_sensitive", "dialect_sensitive", "era_sensitive"}
    key = _load_key(key_path)
    annotations = load_jsonl(annotation_path)
    by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_annotation_ids: set[str] = set()
    seen_annotator_item: set[tuple[str, str]] = set()
    errors: list[str] = []

    for ann in annotations:
        line = ann.get("__line__")
        aid = ann.get("annotation_id")
        item_id = ann.get("item_id")
        annotator_id = ann.get("annotator_id")
        if ann.get("schema_version") != "0.1.0":
            errors.append(f"line {line}: unsupported schema_version {ann.get('schema_version')!r}")
        if not isinstance(annotator_id, str) or not annotator_id:
            errors.append(f"line {line}: annotator_id missing")
        if not isinstance(aid, str) or not aid:
            errors.append(f"line {line}: annotation_id missing")
            continue
        if aid in seen_annotation_ids:
            errors.append(f"line {line}: duplicate annotation_id {aid}")
            continue
        seen_annotation_ids.add(aid)
        if item_id not in key:
            errors.append(f"line {line}: unknown item_id {item_id!r}")
            continue
        if key[item_id].get("mode") == "repair":
            errors.append(f"line {line}: repair packet annotations require qualitative preservation review, not A/B vote aggregation")
            continue
        annotator_item = (str(annotator_id), str(item_id))
        if annotator_item in seen_annotator_item:
            errors.append(f"line {line}: annotator {annotator_id!r} voted more than once on {item_id}")
        seen_annotator_item.add(annotator_item)
        if ann.get("blind") is not True:
            errors.append(f"line {line}: promotion-grade annotation must declare blind=true")
        choice = ann.get("choice")
        if choice not in {"A", "B", "tie", "context_dependent"}:
            errors.append(f"line {line}: invalid choice {choice!r}")
            continue
        strength = ann.get("strength")
        if strength not in allowed_strengths:
            errors.append(f"line {line}: invalid strength {strength!r}")
        if choice in {"tie", "context_dependent"} and strength != "na":
            errors.append(f"line {line}: tie/context_dependent annotation must use strength=na")
        dims = ann.get("dimensions")
        if not isinstance(dims, list) or not dims:
            errors.append(f"line {line}: dimensions must be non-empty")
        elif any(x not in allowed_dims for x in dims):
            errors.append(f"line {line}: unknown judgment dimension in {dims}")
        flags = ann.get("flags", [])
        if not isinstance(flags, list) or any(x not in allowed_flags for x in flags):
            errors.append(f"line {line}: invalid annotation flags {flags!r}")
        canonical = _canonical_choice(choice, key[item_id])
        by_item[item_id].append({**clean_internal(ann), "canonical_choice": canonical})

    if errors:
        raise ValueError("annotation validation failed:\n- " + "\n- ".join(errors))

    items: dict[str, Any] = {}
    consensus_ready = 0
    disagreement = 0
    for item_id, votes in sorted(by_item.items()):
        counts = Counter(v["canonical_choice"] for v in votes)
        n = len(votes)
        top_choice, top_n = counts.most_common(1)[0]
        frac = top_n / n
        # Shannon entropy in bits is descriptive only; no threshold semantics.
        entropy = -sum((c / n) * math.log2(c / n) for c in counts.values()) if n else 0.0
        ready = n >= min_votes and frac >= consensus and top_choice not in {"context_dependent"}
        if ready:
            consensus_ready += 1
        else:
            disagreement += 1
        items[item_id] = {
            "n": n,
            "canonical_vote_counts": dict(sorted(counts.items())),
            "top_choice": top_choice,
            "top_fraction": round(frac, 6),
            "entropy_bits": round(entropy, 6),
            "consensus_ready": ready,
            "provisional_gold": key[item_id].get("gold_canonical"),
            "provisional_evidence_class": key[item_id].get("evidence_class"),
            "flags": dict(sorted(Counter(flag for v in votes for flag in v.get("flags", [])).items())),
        }

    return {
        "annotations": len(annotations),
        "items_annotated": len(items),
        "min_votes": min_votes,
        "consensus_threshold": consensus,
        "consensus_ready_items": consensus_ready,
        "needs_review_or_disagreement": disagreement,
        "items": items,
        "note": "Consensus-ready is an adjudication input, not an automatic gold overwrite.",
    }


STATE_CORPUS = ROOT / "assets/regression-corpora/prose-state-semantics/cases.jsonl"
STATE_FIELDS = {
    "claims": ("target", "layer", "holder", "mode", "truth", "polarity", "acquisition", "value"),
    "state_findings": ("pointer", "status"),
    "impacts": ("node", "status"),
}


def build_state_blind(corpus: Path, output: Path, key_output: Path) -> dict[str, Any]:
    """Keep raw-prose tasks separate from provisional, author-created semantic oracles."""
    paths = [corpus.resolve(), output.resolve(), key_output.resolve()]
    if len(set(paths)) != 3 or output.exists() or key_output.exists():
        raise ValueError("use distinct fresh packet/key paths; corpus cannot be overwritten")
    rows = load_jsonl(corpus)
    ids = [row["case_id"] for row in rows]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("semantic corpus needs unique nonempty case IDs")
    packets, keys = [], []
    for row in rows:
        if set(row["input"]) - {"sources", "state", "dependencies", "revision", "branch"}:
            raise ValueError(f"{row['case_id']}: unexpected input metadata; keep annotations/gold outside the packet")
        if not isinstance(row["input"].get("sources"), dict) or not all(isinstance(text, str) for text in row["input"]["sources"].values()):
            raise ValueError(f"{row['case_id']}: sources must be named raw text")
        packets.append({"case_id": row["case_id"], "input": row["input"],
                        "task": "若 input 含 revision，只分析全部后续判断的修订影响（impacts）；否则从正文独立提取有后续意义的持久退出状态（claims）并复核已有状态、发现遗漏（state_findings）。未使用的数组为空。区分世界事实、角色认知与读者暴露，不要将言说内容直接当事实。保留会影响行动的错误信念；不把临时动作或已有状态的重复叙述当成新的持久变化。",
                        "response_fields": {group: list(fields) + ["evidence"] for group, fields in STATE_FIELDS.items()},
                        "evidence_contract": "每项 evidence 为 source/start_line/end_line/quote；source 使用 input.sources 的键，行号从1起，quote 必须是完整所选行。targets 使用自然语言稳定命题；释义需评审者先对齐后再计分。"})
        keys.append({"case_id": row["case_id"], "category": row["category"],
                     "sources": row["input"]["sources"], "expected": row["expected"],
                     "oracle_status": "provisional-original-seed"})
    write_jsonl(output, packets)
    write_jsonl(key_output, keys)
    return {"items": len(rows), "packet": str(output), "key": str(key_output),
            "note": "Gold-free raw prose packet. This is a provisional seed suite, not independent human consensus or private holdout."}


def score_state_responses(responses_path: Path, key_path: Path) -> dict[str, Any]:
    keys = load_jsonl(key_path)
    key = {row["case_id"]: row for row in keys}
    if len(key) != len(keys) or not key:
        raise ValueError("semantic key has duplicate IDs or is empty")
    answers: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(responses_path):
        cid = row["case_id"]
        if cid not in key or cid in answers:
            raise ValueError(f"unknown or duplicate semantic response: {cid}")
        answers[cid] = row
    totals = {group: Counter(tp=0, fp=0, fn=0) for group in STATE_FIELDS}
    cases = []
    for cid, oracle in key.items():
        response = answers.get(cid, {})
        case_ok = cid in answers
        for group, fields in STATE_FIELDS.items():
            def signature(item: dict[str, Any]) -> str:
                return json.dumps([item[field] for field in fields], ensure_ascii=False, sort_keys=True)
            expected = {signature(item): item for item in oracle["expected"].get(group, [])}
            items = response.get(group, [])
            if not isinstance(items, list):
                raise ValueError(f"{cid}: {group} must be a list")
            predictions = {signature(item): item for item in items}
            if len(predictions) != len(items):
                raise ValueError(f"{cid}: duplicate {group} prediction")
            matched = set()
            for sig, item in predictions.items():
                evs = item.get("evidence", [])
                valid = bool(evs)
                for ev in evs:
                    lines = oracle["sources"].get(ev.get("source"), "").splitlines()
                    start, end = ev.get("start_line", 0), ev.get("end_line", 0)
                    valid = valid and isinstance(start, int) and isinstance(end, int) and 1 <= start <= end <= len(lines)
                    if valid:
                        valid = ev.get("quote") == "\n".join(lines[start - 1:end])
                # Correct categorical labels with unrelated (but authentic) evidence do not count.
                required = expected.get(sig, {}).get("evidence", [])
                grounded = valid and all(any(ev.get("source") == need["source"] and
                                            ev.get("start_line", 0) <= need["start_line"] and
                                            ev.get("end_line", 0) >= need["end_line"] for ev in evs)
                                         for need in required)
                if sig in expected and grounded:
                    matched.add(sig)
            counts = Counter(tp=len(matched), fp=len(predictions) - len(matched), fn=len(expected) - len(matched))
            totals[group].update(counts)
            case_ok = case_ok and not counts["fp"] and not counts["fn"]
        cases.append({"case_id": cid, "category": oracle["category"], "exact_grounded_match": case_ok})
    metrics = {}
    for group, counts in totals.items():
        tp, fp, fn = (counts[name] for name in ("tp", "fp", "fn"))
        metrics[group] = {**counts, "precision": tp / (tp + fp) if tp + fp else None,
                          "recall": tp / (tp + fn) if tp + fn else None,
                          "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}
    return {"cases": cases, "metrics": metrics, "missing_cases": sorted(set(key) - set(answers)),
            "all_cases_exact": all(row["exact_grounded_match"] for row in cases),
            "note": "Extraction, unsupported-state, and revision-impact metrics are separate. Seed/oracle smoke tests do not establish real prose comprehension accuracy. Paraphrase alignment requires independent review."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Chinese Narrative Behavioral Evaluation tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate a contrast-family JSONL corpus")
    p_validate.add_argument("corpus", nargs="?", type=Path, default=DEFAULT_CORPUS)
    p_validate.add_argument("--allow-private-holdout", action="store_true", help="allow external private_holdout families")
    p_validate.add_argument("--json", action="store_true")

    p_blind = sub.add_parser("build-blind", help="build a gold-free generator packet plus separate answer key")
    p_blind.add_argument("corpus", nargs="?", type=Path, default=DEFAULT_CORPUS)
    p_blind.add_argument("--out", type=Path, required=True, help="generator-visible JSONL packet")
    p_blind.add_argument("--key-out", type=Path, required=True, help="separate evaluator-only JSONL key")
    p_blind.add_argument("--mode", choices=["recognition", "diagnosis", "repair"], default="recognition")
    p_blind.add_argument("--seed", type=int, default=0)
    p_blind.add_argument("--split", action="append", choices=["example", "dev", "challenge", "private_holdout"], default=[])
    p_blind.add_argument("--allow-private-holdout", action="store_true")
    p_blind.add_argument("--json", action="store_true")

    p_score = sub.add_parser("score", help="score categorical A/B/tie/context-dependent responses against a blind key")
    p_score.add_argument("responses", type=Path)
    p_score.add_argument("key", type=Path)
    p_score.add_argument("--json", action="store_true")

    p_ann = sub.add_parser("aggregate-annotations", help="aggregate blinded human annotations without overwriting gold")
    p_ann.add_argument("annotations", type=Path)
    p_ann.add_argument("key", type=Path)
    p_ann.add_argument("--min-votes", type=int, default=3)
    p_ann.add_argument("--consensus", type=float, default=0.8)
    p_ann.add_argument("--json", action="store_true")

    p_state = sub.add_parser("build-state-blind", help="build raw-prose reconciliation/revision tasks without semantic gold")
    p_state.add_argument("corpus", nargs="?", type=Path, default=STATE_CORPUS)
    p_state.add_argument("--out", type=Path, required=True)
    p_state.add_argument("--key-out", type=Path, required=True)
    p_state_score = sub.add_parser("score-state", help="score grounded extraction, unsupported state and revision impact separately")
    p_state_score.add_argument("responses", type=Path)
    p_state_score.add_argument("key", type=Path)

    args = parser.parse_args()

    try:
        if args.command == "build-state-blind":
            print(json.dumps(build_state_blind(args.corpus, args.out, args.key_out), ensure_ascii=False, indent=2))
            return 0
        if args.command == "score-state":
            print(json.dumps(score_state_responses(args.responses, args.key), ensure_ascii=False, indent=2))
            return 0
        if args.command == "validate":
            errors, warnings, summary = validate_corpus(args.corpus, allow_private_holdout=args.allow_private_holdout)
            result = {"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for warning in warnings:
                    print(f"WARNING: {warning}")
                for error in errors:
                    print(f"ERROR: {error}")
                print(f"summary: {summary.get('families', 0)} families, {summary.get('variants', 0)} variants, {len(errors)} error(s), {len(warnings)} warning(s)")
            return 1 if errors else 0

        if args.command == "build-blind":
            splits = set(args.split or ["dev"])
            result = build_blind(args.corpus, args.out, args.key_out, mode=args.mode, seed=args.seed, splits=splits, allow_private_holdout=args.allow_private_holdout)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"built {result['items']} item(s); skipped {result['skipped']}; packet={result['packet']} key={result['key']}")
            return 0

        if args.command == "score":
            result = score_responses(args.responses, args.key)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "aggregate-annotations":
            result = aggregate_annotations(args.annotations, args.key, min_votes=args.min_votes, consensus=args.consensus)
            print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
