from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from app.rag import workflow


# ---------- Fakes ----------

class FakeLLM:
    """Stands in for ChatOpenAI. Returns scripted answers in order.

    decisions: answers for structured calls (router and graders), e.g. {"route": "kb"}
    texts:     answers for plain calls (rewrite and answer generation)
    """

    def __init__(self, decisions=(), texts=()):
        self.decisions = list(decisions)
        self.texts = list(texts)

    def with_structured_output(self, schema, method=None):
        fake = self

        class StructuredFake:
            def invoke(self, prompt):
                return schema(**fake.decisions.pop(0))

        return StructuredFake()

    def invoke(self, prompt):
        return SimpleNamespace(content=self.texts.pop(0))

    def all_answers_used(self):
        return not self.decisions and not self.texts


def doc(text, source="data/sample_kb/vpn_guide.md"):
    return Document(page_content=text, metadata={"source": source})


KB = {"route": "kb"}
DIRECT = {"route": "direct"}
GOOD = {"grade": "good"}
WEAK = {"grade": "weak"}

WEB_RESULT = {
    "answer": "Use the vendor app to re-register the token.",
    "results": [
        {"title": "Token guide", "url": "https://example.com/token", "content": "Steps..."},
    ],
}


@pytest.fixture
def agent(mocker):
    """Replace OpenAI, Pinecone and Tavily with fakes, and return them for checking."""

    def setup(decisions=(), texts=(), docs=(), web_result=None):
        fake_llm = FakeLLM(decisions, texts)
        retriever = mocker.Mock()
        retriever.invoke.return_value = list(docs)
        web = mocker.Mock()
        web.invoke.return_value = web_result or WEB_RESULT
        mocker.patch.object(workflow, "llm", return_value=fake_llm)
        mocker.patch.object(workflow, "get_retriever", return_value=retriever)
        mocker.patch.object(workflow, "web_search_tool", return_value=web)
        return SimpleNamespace(llm=fake_llm, retriever=retriever, web=web)

    return setup


# ---------- Decision functions (no fakes needed) ----------

def test_router_sends_kb_questions_to_retrieval():
    assert workflow.route_after_router({"source_used": "kb"}) == "retrieve_kb"


def test_router_sends_everything_else_to_direct_answer():
    assert workflow.route_after_router({"source_used": "direct"}) == "direct_answer"


def test_good_kb_evidence_goes_to_answer_generation():
    assert workflow.after_kb({"kb_grade": "good"}) == "generate_from_kb"


def test_weak_kb_evidence_falls_back_to_web():
    assert workflow.after_kb({"kb_grade": "weak"}) == "search_web"


def test_good_web_evidence_goes_to_answer_generation():
    state = {"web_grade": "good", "retry_count": 0}
    assert workflow.after_web(state) == "generate_from_web"


def test_weak_web_evidence_triggers_rewrite_while_retries_remain(monkeypatch):
    monkeypatch.setattr(workflow.settings, "max_retries", 2)
    state = {"web_grade": "weak", "retry_count": 1}
    assert workflow.after_web(state) == "rewrite_query"


def test_weak_web_evidence_stops_when_retries_are_used_up(monkeypatch):
    monkeypatch.setattr(workflow.settings, "max_retries", 2)
    state = {"web_grade": "weak", "retry_count": 2}
    assert workflow.after_web(state) == "insufficient"


def test_add_trace_does_not_change_the_original_state():
    state = {"trace": ["step 1"]}
    new_trace = workflow.add_trace(state, "step 2")
    assert new_trace == ["step 1", "step 2"]
    assert state["trace"] == ["step 1"]


# ---------- Full agent runs (fake LLM, retriever and web search) ----------

def test_greeting_is_answered_directly_without_retrieval(agent):
    fakes = agent(decisions=[DIRECT], texts=["Hello! How can I help?"])

    result = workflow.ask("Hi there")

    assert result["source_used"] == "direct"
    assert result["answer"] == "Hello! How can I help?"
    fakes.retriever.invoke.assert_not_called()
    fakes.web.invoke.assert_not_called()
    assert fakes.llm.all_answers_used()


def test_good_kb_evidence_is_answered_from_documents_with_citations(agent):
    fakes = agent(
        decisions=[KB, GOOD],
        texts=["Open the VPN client and sign in."],
        docs=[doc("VPN steps...")],
    )

    result = workflow.ask("How do I connect to the VPN?")

    assert result["source_used"] == "private_kb"
    expected = [{"title": "vpn_guide.md", "url": "", "type": "private_kb"}]
    assert result["citations"] == expected
    fakes.web.invoke.assert_not_called()
    assert fakes.llm.all_answers_used()


def test_chunks_from_the_same_file_produce_one_citation(agent):
    agent(
        decisions=[KB, GOOD],
        texts=["Answer"],
        docs=[doc("part 1"), doc("part 2")],
    )

    result = workflow.ask("How do I connect to the VPN?")

    assert len(result["citations"]) == 1


def test_weak_kb_evidence_falls_back_to_web_answer(agent):
    fakes = agent(
        decisions=[KB, WEAK, GOOD],
        texts=["According to the vendor site..."],
        docs=[doc("unrelated text")],
    )

    result = workflow.ask("What is the latest token app version?")

    assert result["source_used"] == "web_search"
    assert result["citations"][0]["url"] == "https://example.com/token"
    fakes.web.invoke.assert_called_once()
    assert fakes.llm.all_answers_used()


def test_rewritten_query_is_used_for_the_retry(agent, monkeypatch):
    monkeypatch.setattr(workflow.settings, "max_retries", 1)
    fakes = agent(
        decisions=[KB, WEAK, WEAK, GOOD],
        texts=["reset hardware token admin console", "Here is how to reset it."],
        docs=[doc("token reset steps")],
    )

    result = workflow.ask("token broken")

    assert result["source_used"] == "private_kb"
    assert result["retry_count"] == 1
    searched = [call.args[0] for call in fakes.retriever.invoke.call_args_list]
    assert searched == ["token broken", "reset hardware token admin console"]
    assert fakes.llm.all_answers_used()


def test_agent_gives_up_honestly_when_all_evidence_is_weak(agent, monkeypatch):
    monkeypatch.setattr(workflow.settings, "max_retries", 1)
    fakes = agent(
        decisions=[KB, WEAK, WEAK, WEAK, WEAK],
        texts=["rewritten question"],
        docs=[doc("unrelated text")],
    )

    result = workflow.ask("Something nobody documented")

    assert result["source_used"] == "insufficient_evidence"
    assert "couldn't find enough reliable evidence" in result["answer"]
    assert result["retry_count"] == 1
    assert fakes.retriever.invoke.call_count == 2
    assert any("Stopped" in step for step in result["trace"])
    assert fakes.llm.all_answers_used()