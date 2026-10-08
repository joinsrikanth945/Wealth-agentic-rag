"""Scoring rules for the answer-quality evaluation.

Pure functions, with no API calls, so the scorer itself can be unit-tested.
"""
import re


def normalize(text: str) -> str:
    """Lower-case and collapse whitespace, so formatting differences don't matter."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def fact_present(fact, text: str) -> bool:
    """A fact is a string, or a list of accepted alternatives (any one is enough)."""
    alternatives = fact if isinstance(fact, list) else [fact]
    normalized = normalize(text)
    return any(normalize(alt) in normalized for alt in alternatives)


def cited_sources(result: dict) -> list[str]:
    return [c.get("title", "") for c in result.get("citations", [])]


def retrieved_text(result: dict) -> str:
    return " ".join(getattr(d, "page_content", "") for d in result.get("kb_docs", []))


def score_case(case: dict, result: dict) -> dict:
    """Score one agent result against one evaluation case.

    Each check is True (pass), False (fail) or None (not applicable).
    """
    answer = result.get("answer", "")
    path = result.get("source_used", "")
    facts = case.get("expected_facts", [])
    forbidden = case.get("forbidden_facts", [])
    expected_source = case.get("expected_source")
    expected_path = case.get("expected_path")

    checks = {
        "facts": all(fact_present(f, answer) for f in facts) if facts else None,
        "source": (
            any(expected_source.lower() in s.lower() for s in cited_sources(result))
            if expected_source else None
        ),
        "path": (path in expected_path) if expected_path else None,
        "grounded": (
            all(fact_present(f, retrieved_text(result)) for f in facts)
            if facts and path == "private_kb" else None
        ),
        "no_invention": (
            not any(fact_present(f, answer) for f in forbidden) if forbidden else None
        ),
    }
    applicable = [v for v in checks.values() if v is not None]
    return {
        "id": case["id"],
        "question": case["question"],
        "checks": checks,
        "passed": all(applicable),
        "path": path,
        "answer": answer,
        "sources": cited_sources(result),
    }


def summarize(scores: list[dict]) -> dict:
    """Pass rate overall and per check."""
    summary = {"cases": len(scores), "passed": sum(s["passed"] for s in scores)}
    for check in ("facts", "source", "path", "grounded", "no_invention"):
        values = [s["checks"][check] for s in scores if s["checks"][check] is not None]
        summary[check] = (sum(values), len(values))
    summary["pass_rate"] = summary["passed"] / summary["cases"] if scores else 0.0
    return summary
