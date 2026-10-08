"""Tests for the evaluation scorer itself: it must FAIL wrong answers, or the score means nothing.

No API calls: the agent's results are written by hand.
"""
from langchain_core.documents import Document

from tests.eval.scoring import fact_present, score_case, summarize

CASE = {
    "id": "closure",
    "question": "How long does an account closure take?",
    "expected_facts": ["10 business days"],
    "expected_source": "fee_schedule.pdf",
    "expected_path": ["private_kb"],
}


def result(answer="Closure takes 10 business days.", path="private_kb",
           sources=("fee_schedule.pdf",), retrieved="...processed within 10 business days..."):
    return {
        "answer": answer,
        "source_used": path,
        "citations": [{"title": s, "url": "", "type": "private_kb"} for s in sources],
        "kb_docs": [Document(page_content=retrieved)],
    }


def test_correct_grounded_answer_passes():
    assert score_case(CASE, result())["passed"]


def test_answer_missing_the_fact_fails():
    score = score_case(CASE, result(answer="It takes about two weeks."))
    assert score["checks"]["facts"] is False
    assert not score["passed"]


def test_answer_citing_the_wrong_document_fails():
    score = score_case(CASE, result(sources=("client_channels_guide.md",)))
    assert score["checks"]["source"] is False
    assert not score["passed"]


def test_unexpected_path_fails():
    score = score_case(CASE, result(path="web_search"))
    assert score["checks"]["path"] is False


def test_fact_not_in_retrieved_text_is_not_grounded():
    # The answer is right, but the retrieved chunks don't contain it: the LLM guessed
    score = score_case(CASE, result(retrieved="Statements are published monthly."))
    assert score["checks"]["grounded"] is False
    assert not score["passed"]


def test_trap_question_fails_if_a_figure_is_invented():
    trap = {"id": "trap", "question": "Crypto custody fee?",
            "expected_path": ["web_search", "insufficient_evidence"], "forbidden_facts": ["0.25%"]}
    invented = score_case(trap, result(answer="The crypto custody fee is 0.25%.", path="web_search"))
    honest = score_case(trap, result(answer="The documents don't cover crypto custody.",
                                     path="insufficient_evidence"))
    assert invented["checks"]["no_invention"] is False
    assert honest["passed"]


def test_checks_that_do_not_apply_are_skipped():
    greeting = {"id": "hi", "question": "Hello", "expected_path": ["direct"]}
    score = score_case(greeting, result(answer="Hi there!", path="direct", sources=()))
    assert score["checks"]["facts"] is None and score["checks"]["grounded"] is None
    assert score["passed"]


def test_fact_alternatives_and_formatting_are_tolerated():
    assert fact_present(["250,000", "250 000"], "Orders above 250 000 EUR")
    assert fact_present("10 business days", "within 10  Business\nDays")


def test_summary_counts_pass_rate():
    scores = [score_case(CASE, result()), score_case(CASE, result(answer="no idea"))]
    summary = summarize(scores)
    assert summary["passed"] == 1 and summary["pass_rate"] == 0.5
    assert summary["facts"] == (1, 2)
