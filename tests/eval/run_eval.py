"""Answer-quality evaluation: asks the REAL agent known questions and scores the answers.

Uses real OpenAI, Pinecone and Tavily, so each run costs a few cents.
It never runs with plain `pytest` or in the CI pipeline.

    python tests/eval/run_eval.py                  # uses the public-demo namespace
    python tests/eval/run_eval.py --threshold 0.9  # stricter quality gate
    python tests/eval/run_eval.py --only scanned   # only cases whose id contains "scanned"
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from tests.eval.scoring import score_case, summarize  # noqa: E402

MARK = {True: "PASS", False: "FAIL", None: "  - "}


def load_cases(only: str | None = None) -> list[dict]:
    cases = yaml.safe_load((HERE / "questions.yaml").read_text(encoding="utf-8"))
    return [c for c in cases if not only or only in c["id"]]


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def write_report(scores, summary, threshold, namespace, seconds) -> Path:
    lines = [
        "# Answer-quality evaluation report",
        "",
        f"- **Date:** {dt.datetime.now():%Y-%m-%d %H:%M}",
        f"- **Commit:** `{git_commit()}`",
        f"- **Pinecone namespace:** `{namespace}`",
        f"- **Duration:** {seconds:.0f} s",
        f"- **Result:** {summary['passed']}/{summary['cases']} cases passed "
        f"({summary['pass_rate']:.0%}); threshold {threshold:.0%} → "
        f"**{'PASS' if summary['pass_rate'] >= threshold else 'FAIL'}**",
        "",
        "| Check | Passed |",
        "|---|---|",
    ]
    for check in ("facts", "source", "path", "grounded", "no_invention"):
        ok, total = summary[check]
        lines.append(f"| {check} | {ok}/{total} |")
    lines += ["", "| Case | Facts | Source | Path | Grounded | No invention | Agent path |", "|---|---|---|---|---|---|---|"]
    for s in scores:
        c = s["checks"]
        lines.append(
            f"| {s['id']} | {MARK[c['facts']]} | {MARK[c['source']]} | {MARK[c['path']]} | "
            f"{MARK[c['grounded']]} | {MARK[c['no_invention']]} | {s['path']} |"
        )
    failures = [s for s in scores if not s["passed"]]
    if failures:
        lines += ["", "## Failures", ""]
        for s in failures:
            lines += [
                f"### {s['id']}",
                f"- **Question:** {s['question']}",
                f"- **Agent path:** {s['path']}",
                f"- **Sources cited:** {', '.join(s['sources']) or 'none'}",
                f"- **Answer:** {s['answer'][:600]}",
                "",
            ]
    path = HERE / "eval_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv=None, ask=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=0.85, help="minimum pass rate (default 0.85)")
    parser.add_argument("--namespace", default=os.getenv("PINECONE_NAMESPACE", "public-demo"))
    parser.add_argument("--only", help="run only cases whose id contains this text")
    args = parser.parse_args(argv)

    # Settings are read when the app is imported, so set the namespace first
    os.environ["PINECONE_NAMESPACE"] = args.namespace
    if ask is None:
        from app.rag.workflow import ask

    cases = load_cases(args.only)
    print(f"Running {len(cases)} evaluation cases against namespace '{args.namespace}'...\n")
    started = time.time()
    scores = []
    for case in cases:
        try:
            result = ask(case["question"])
        except Exception as exc:  # a crash counts as a failed case, not a crashed run
            result = {"answer": f"ERROR: {exc}", "source_used": "error", "citations": [], "kb_docs": []}
        score = score_case(case, result)
        scores.append(score)
        c = score["checks"]
        print(f"{'PASS' if score['passed'] else 'FAIL'}  {score['id']:<28} "
              f"facts={MARK[c['facts']].strip() or '-'} source={MARK[c['source']].strip() or '-'} "
              f"path={MARK[c['path']].strip() or '-'} grounded={MARK[c['grounded']].strip() or '-'} "
              f"({score['path']})")

    summary = summarize(scores)
    report = write_report(scores, summary, args.threshold, args.namespace, time.time() - started)
    print(f"\n{summary['passed']}/{summary['cases']} passed ({summary['pass_rate']:.0%}), "
          f"threshold {args.threshold:.0%}. Report: {report.relative_to(ROOT)}")
    return 0 if summary["pass_rate"] >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
