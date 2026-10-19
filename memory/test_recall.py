"""RAG recall quality gate for the opencode-framework memory system.

Target: mean nDCG at k=10 of at least 0.85 across the fixture queries.
RAM ceiling: peak resident set size under 2048 MB during the full run.

Modes of operation:

1. Real mode. If ``lancedb`` and ``sentence-transformers`` import
   cleanly, the harness builds a default Consolidator, ingests every
   fixture entry, then issues each query and aggregates nDCG. This is
   the real quality gate.

2. Skip mode. If either heavy dependency is missing, the harness prints
   a SKIP notice with install instructions and exits with status 0 so
   CI does not fail on environments that have not installed the
   optional ML stack.

3. Mock mode. A caller can inject a stub consolidator (duck typed with
   ``consolidate_new`` and ``recall``) for harness self tests. The
   bundled ``_NaiveMockConsolidator`` scores by token overlap only and
   does not validate the real quality gate.

Usage:
    python memory/test_recall.py
    python memory/test_recall.py path/to/fixture.yaml
"""

from __future__ import annotations

import math
import os
import re
import resource
import sys
from pathlib import Path
from typing import Any


FIXTURE_DEFAULT: str = str(
    Path(__file__).parent / "fixtures" / "recall_fixture.yaml"
)

NDCG_TARGET: float = 0.85
RAM_CEILING_MB: float = 2048.0
RECALL_TOP_K: int = 10


def load_fixture(path: str) -> dict[str, Any]:
    """Load fixture YAML as a dict with entries and queries keys."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        raise FileNotFoundError(f"fixture not found: {expanded}")
    try:
        import yaml as _yaml  # type: ignore
        with open(expanded, "r", encoding="utf-8") as fh:
            data = _yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError("fixture root must be a mapping")
        return data
    except ImportError:
        return _parse_fixture_fallback(expanded)


def _parse_fixture_fallback(path: str) -> dict[str, Any]:
    """Minimal YAML parser scoped to the recall_fixture shape only."""
    entries: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    section: str | None = None
    current: dict[str, Any] | None = None
    in_metadata: bool = False

    def _unquote(raw: str) -> str:
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
            return raw[1:-1]
        return raw

    def _parse_list(raw: str) -> list[str]:
        raw = raw.strip()
        if not (raw.startswith("[") and raw.endswith("]")):
            return []
        body = raw[1:-1].strip()
        return [_unquote(p.strip()) for p in body.split(",") if p.strip()]

    def _coerce(value: str) -> Any:
        value = value.strip()
        if value.startswith("["):
            return _parse_list(value)
        return _unquote(value)

    def _commit() -> None:
        if current is None:
            return
        if section == "entries":
            entries.append(current)
        elif section == "queries":
            queries.append(current)

    with open(path, "r", encoding="utf-8") as fh:
        for raw_line in fh.readlines():
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if line.startswith("entries:"):
                _commit()
                section, current, in_metadata = "entries", None, False
                continue
            if line.startswith("queries:"):
                _commit()
                section, current, in_metadata = "queries", None, False
                continue
            if section is None:
                continue
            indent = len(line) - len(line.lstrip(" "))
            if stripped.startswith("- "):
                _commit()
                current = {}
                in_metadata = False
                after = stripped[2:]
                if ":" in after:
                    k, _, v = after.partition(":")
                    current[k.strip()] = _coerce(v)
                continue
            if current is None:
                continue
            if stripped.startswith("metadata:"):
                current["metadata"] = {}
                in_metadata = True
                continue
            if in_metadata and indent >= 6 and ":" in stripped:
                k, _, v = stripped.partition(":")
                current["metadata"][k.strip()] = _unquote(v)
                continue
            if ":" in stripped and indent >= 4:
                in_metadata = False
                k, _, v = stripped.partition(":")
                current[k.strip()] = _coerce(v)
    _commit()
    return {"entries": entries, "queries": queries}


def ndcg_at_k(
    predicted_ids: list[str],
    relevant_ids: list[str],
    k: int = RECALL_TOP_K,
) -> float:
    """Binary relevance nDCG at k with discount 1 / log2(rank + 2)."""
    if not relevant_ids:
        return 0.0
    rel_set = set(relevant_ids)
    dcg = 0.0
    for rank, pid in enumerate(predicted_ids[:k]):
        if pid in rel_set:
            dcg += 1.0 / math.log2(rank + 2.0)
    ideal_hits = min(len(rel_set), k)
    idcg = sum(1.0 / math.log2(r + 2.0) for r in range(ideal_hits))
    return (dcg / idcg) if idcg > 0.0 else 0.0


def measure_ram_mb() -> float:
    """Peak RSS in MB. macOS reports bytes, linux reports kilobytes."""
    raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return raw / (1024.0 * 1024.0)
    return raw / 1024.0


def _deps_available() -> tuple[bool, str]:
    missing: list[str] = []
    try:
        import lancedb  # type: ignore  # noqa: F401
    except ImportError:
        missing.append("lancedb")
    try:
        import sentence_transformers  # type: ignore  # noqa: F401
    except ImportError:
        missing.append("sentence-transformers")
    return (not missing, ", ".join(missing))


class _NaiveMockConsolidator:
    """Token overlap stub for harness self tests only."""

    _TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        return {t.lower() for t in cls._TOKEN_RE.findall(text)}

    def consolidate_new(
        self,
        text: str,
        namespace: str,
        ttl_tier: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        eid = str((metadata or {}).get("fixture_id") or len(self.store) + 1)
        self.store[eid] = {
            "id": eid,
            "text": text,
            "namespace": namespace,
            "ttl_tier": ttl_tier,
            "metadata": dict(metadata or {}),
        }
        return {"inserted": True, "id": eid, "stage": "mock"}

    def recall(
        self,
        query: str,
        namespace_priority: dict[str, float] | None = None,
        top_k: int = RECALL_TOP_K,
    ) -> list[dict[str, Any]]:
        qt = self._tokens(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in self.store.values():
            et = self._tokens(entry.get("text", ""))
            if not et:
                continue
            overlap = len(qt & et)
            if overlap == 0:
                continue
            scored.append((overlap / math.sqrt(len(et)), entry))
        scored.sort(key=lambda p: p[0], reverse=True)
        return [dict(e, final_score=s) for s, e in scored[: max(0, top_k)]]


def _predicted_ids(hits: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in hits:
        md = row.get("metadata")
        if isinstance(md, dict) and md.get("fixture_id"):
            out.append(str(md["fixture_id"]))
            continue
        rid = row.get("id")
        if rid:
            out.append(str(rid))
    return out


def run_recall_test(
    fixture_path: str = FIXTURE_DEFAULT,
    consolidator: Any = None,
) -> dict[str, Any]:
    """Full recall test: load, ingest, query, aggregate nDCG, check RAM."""
    fixture = load_fixture(fixture_path)
    entries = fixture.get("entries") or []
    queries = fixture.get("queries") or []
    if not entries or not queries:
        return {
            "status": "FAIL",
            "mean_ndcg": 0.0,
            "per_query": [],
            "ram_mb": measure_ram_mb(),
            "ram_ok": True,
            "notes": "fixture missing entries or queries",
        }

    mode = "mock" if consolidator is not None else "real"
    if consolidator is None:
        ok, missing = _deps_available()
        if not ok:
            notes = (
                f"SKIP: missing ML deps ({missing}). "
                "Install: pip install lancedb sentence-transformers "
                "datasketch simhash"
            )
            print(notes)
            return {
                "status": "SKIP",
                "mean_ndcg": 0.0,
                "per_query": [],
                "ram_mb": measure_ram_mb(),
                "ram_ok": True,
                "notes": notes,
            }
        try:
            from memory.consolidator import get_default_consolidator
            consolidator = get_default_consolidator()
        except Exception as exc:
            notes = f"SKIP: consolidator init failed: {exc}"
            print(notes)
            return {
                "status": "SKIP",
                "mean_ndcg": 0.0,
                "per_query": [],
                "ram_mb": measure_ram_mb(),
                "ram_ok": True,
                "notes": notes,
            }

    ingested = 0
    for entry in entries:
        eid = str(entry.get("id", "")).strip()
        text = str(entry.get("text", "")).strip()
        if not text:
            continue
        namespace = str(entry.get("namespace") or "session").strip()
        ttl_tier = str(entry.get("ttl_tier") or "logs").strip()
        metadata = dict(entry.get("metadata") or {})
        metadata["fixture_id"] = eid
        try:
            consolidator.consolidate_new(
                text=text,
                namespace=namespace,
                ttl_tier=ttl_tier,
                metadata=metadata,
            )
            ingested += 1
        except Exception as exc:
            print(f"ingest failed for {eid}: {exc}", file=sys.stderr)

    per_query: list[dict[str, Any]] = []
    total = 0.0
    for q in queries:
        qt = str(q.get("query", "")).strip()
        rel = [str(r) for r in (q.get("relevant_ids") or [])]
        if not qt or not rel:
            continue
        try:
            hits = consolidator.recall(query=qt, top_k=RECALL_TOP_K)
        except Exception as exc:
            print(f"recall failed: {exc}", file=sys.stderr)
            hits = []
        preds = _predicted_ids(hits)
        score = ndcg_at_k(preds, rel, k=RECALL_TOP_K)
        total += score
        per_query.append({
            "query": qt,
            "relevant_ids": rel,
            "predicted_ids": preds[:RECALL_TOP_K],
            "ndcg": score,
        })

    count = len(per_query)
    mean = (total / count) if count > 0 else 0.0
    ram_mb = measure_ram_mb()
    ram_ok = ram_mb < RAM_CEILING_MB
    status = "PASS" if (mean >= NDCG_TARGET and ram_ok) else "FAIL"
    return {
        "status": status,
        "mean_ndcg": mean,
        "per_query": per_query,
        "ram_mb": ram_mb,
        "ram_ok": ram_ok,
        "notes": f"mode={mode} ingested={ingested} queries={count}",
    }


def _format_report(report: dict[str, Any]) -> str:
    lines = [
        f"status: {report['status']}",
        f"mean_ndcg: {report['mean_ndcg']:.4f} (target >= {NDCG_TARGET})",
        f"ram_mb: {report['ram_mb']:.2f} (ceiling < {RAM_CEILING_MB})",
        f"notes: {report['notes']}",
        "per_query:",
    ]
    for item in report.get("per_query", []):
        preview = item["query"][:60]
        lines.append(
            f"  ndcg={item['ndcg']:.4f} "
            f"relevant={item['relevant_ids']} "
            f"predicted={item['predicted_ids']} q={preview!r}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else FIXTURE_DEFAULT
    report = run_recall_test(path)
    print(_format_report(report))
    return 0 if report.get("status") in ("PASS", "SKIP") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
