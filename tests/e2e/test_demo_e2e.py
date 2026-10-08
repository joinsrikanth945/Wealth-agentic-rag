"""End-to-end tests: a real browser (Playwright) against a running deployment.

They only run when E2E_BASE_URL is set, so plain `pytest` skips them:

    $env:E2E_BASE_URL = "https://agentic-rag.wittybeach-2baef286.eastus2.azurecontainerapps.io"
    pytest tests/e2e -v

The question tests use the real LLM, so a full run costs about 1-2 cents.
The pipeline runs them after every deployment.
"""
import os
import re

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import Page, expect  # noqa: E402

BASE_URL = os.getenv("E2E_BASE_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set E2E_BASE_URL to run the end-to-end tests")

# Allow for a cold start (the demo scales to zero) plus the agent's LLM calls
PAGE_TIMEOUT = 120_000
ANSWER_TIMEOUT = 120_000


@pytest.fixture
def home(page: Page) -> Page:
    page.goto(BASE_URL, timeout=PAGE_TIMEOUT)
    expect(page.locator("h1")).to_contain_text("Wealth Banking", timeout=PAGE_TIMEOUT)
    return page


def ask(page: Page, question: str) -> None:
    page.locator("#question").fill(question)
    page.get_by_role("button", name="Ask Agent").click()
    wait_for_answer(page)


def wait_for_answer(page: Page) -> None:
    """The 'Final Source' box shows 'Running' while the agent works, then the route taken."""
    expect(page.locator("#sourceUsed")).not_to_have_text(re.compile(r"^(—|Running)$"), timeout=ANSWER_TIMEOUT)


def last_answer(page: Page):
    return page.locator(".message.assistant .bubble").last


# ---------- Page ----------

def test_home_page_shows_heading_and_example_questions(home: Page):
    expect(home.locator(".example")).to_have_count(3)
    expect(home.get_by_role("button", name="How do I register a LumenKey token?")).to_be_visible()
    expect(home.locator("#sourceUsed")).to_have_text("—")


# ---------- Answer paths, through the real UI ----------

def test_example_question_is_answered_from_documents_with_citation_and_trace(home: Page):
    home.get_by_role("button", name="How do I register a LumenKey token?").click()
    wait_for_answer(home)

    expect(home.locator("#sourceUsed")).to_have_text("private_kb")
    expect(last_answer(home)).to_contain_text(re.compile("QR", re.I))
    expect(last_answer(home).locator(".citations")).to_contain_text("secure_access_token_guide")
    expect(home.locator("#trace")).to_contain_text("PRIVATE KB")


def test_greeting_is_answered_directly_without_retrieval(home: Page):
    ask(home, "Hello, good morning!")

    expect(home.locator("#sourceUsed")).to_have_text("direct")
    expect(home.locator("#trace")).to_contain_text("Direct response")
    expect(home.locator("#trace")).not_to_contain_text("retrieval →")


def test_trap_question_is_not_answered_with_an_invented_fee(home: Page):
    """Regression test for issue #1: the general custody fee must not be applied to crypto."""
    ask(home, "What is LumenWealth's custody fee for crypto assets?")

    expect(home.locator("#sourceUsed")).to_have_text(re.compile(r"^(insufficient_evidence|web_search)$"))
    expect(last_answer(home)).not_to_contain_text("0.25%")


# ---------- Upload security ----------

def test_upload_without_admin_key_is_refused(home: Page, tmp_path):
    sample = tmp_path / "note.txt"
    sample.write_text("End-to-end test upload.", encoding="utf-8")

    home.locator("#openUpload").click()
    home.locator("#fileInput").set_input_files(str(sample))
    home.locator("#uploadBtn").click()

    expect(home.locator("#uploadStatus")).to_contain_text("Invalid admin key", timeout=PAGE_TIMEOUT)
