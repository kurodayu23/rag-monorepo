from langchain_core.language_models.fake_chat_models import FakeListChatModel
from app.langchain_engine import query_with_langchain


def test_lcel_passes_separate_question_and_context(monkeypatch):
    observed = []
    class RecordingModel(FakeListChatModel):
        def _call(self, messages, **kwargs):
            observed.append(messages[0].content)
            return super()._call(messages, **kwargs)
    monkeypatch.setattr("langchain_community.chat_models.ChatOllama",
                        lambda **kwargs: RecordingModel(responses=["yes", "Nimbus"]))
    assert query_with_langchain("Codename?", ["Codename: Nimbus"], "test") == "Nimbus"
    assert "Context: - Codename: Nimbus" in observed[0]
    assert "Question: Codename?" in observed[0]
    assert "{'context':" not in observed[0]


def test_lcel_refuses_when_context_is_insufficient(monkeypatch):
    monkeypatch.setattr("langchain_community.chat_models.ChatOllama",
                        lambda **kwargs: FakeListChatModel(responses=["no"]))
    assert "Insufficient information" in query_with_langchain("unknown", ["fact"], "test")
