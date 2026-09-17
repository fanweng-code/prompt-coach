import pytest

from prompt_coach.models import Completion, Mode, ProfileId, RewriteError
from prompt_coach.profiles import get_profile
from prompt_coach.prompts import COMMON_RULES, MODE_RULES, build_system_prompt
from prompt_coach.transformer import PromptTransformer


class RecordingClient:
    requested_model = "configured-model"

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def complete(self, system, user):
        self.calls.append((system, user))
        if self.error:
            raise self.error
        return Completion("合成結果", "fake-model")


@pytest.mark.parametrize("mode", list(Mode))
@pytest.mark.parametrize("profile_id", list(ProfileId))
def test_six_combinations_preserve_input_and_backend(mode, profile_id):
    raw = "  先分析，不要改程式；等我確認。\n保留 D:\\work\\app.py 與 0/10。😀\n"
    client = RecordingClient()
    result = PromptTransformer(client).rewrite(raw, mode, profile_id)
    profile = get_profile(profile_id)
    assert client.calls == [(build_system_prompt(mode, profile), raw)]
    system = client.calls[0][0]
    assert system == "\n\n".join((COMMON_RULES, MODE_RULES[mode], profile.instructions))
    assert result.text == "合成結果"
    assert result.mode == mode and result.profile_id == profile_id
    assert result.requested_model == "configured-model" and result.actual_model == "fake-model"
    assert result.profile_version == "1.0.0" and result.elapsed_s >= 0
    assert result.status == "success"
    assert profile.source_references and profile.last_reviewed == "2026-09-17"


@pytest.mark.parametrize("text", ["", " \n\t", "文" * 20_001, "😀" * 20_001], ids=["empty", "blank", "long-text", "long-emoji"])
def test_invalid_input_never_calls_client(text):
    client = RecordingClient()
    with pytest.raises(RewriteError) as error:
        PromptTransformer(client).rewrite(text, Mode.COMMAND, ProfileId.ASTRA)
    assert error.value.code == "input"
    assert client.calls == []


@pytest.mark.parametrize("char", ["文", "😀"])
def test_exact_unicode_limit_is_accepted(char):
    client = RecordingClient()
    PromptTransformer(client).rewrite(char * 20_000, Mode.COMMAND, ProfileId.ASTRA)
    assert len(client.calls) == 1 and client.calls[0][1] == char * 20_000


def test_client_failure_is_not_retried():
    client = RecordingClient(RewriteError("timeout"))
    with pytest.raises(RewriteError, match="逾時"):
        PromptTransformer(client).rewrite("整理", Mode.THOUGHT, ProfileId.GENERIC)
    assert len(client.calls) == 1
