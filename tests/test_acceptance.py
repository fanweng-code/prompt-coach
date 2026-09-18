import hashlib
import json

import httpx
import pytest

from scripts import quality_acceptance as qa
from prompt_coach.models import Mode, ProfileId
from prompt_coach.profiles import get_profile
from prompt_coach import prompts


def prepare(tmp_path, *, seed=False, repeats=1):
    return qa.prepare(tmp_path / "batch", "http://127.0.0.1:8080/v1",
                      qa.ORNITH_MODEL if seed else "test-model",
                      qa.ORNITH_VERSION if seed else "test-runtime", 60, repeats, seed)


def test_policy_identity_covers_common_mode_and_profile(monkeypatch):
    profile = get_profile(ProfileId.ASTRA)
    before = prompts.policy_snapshot(Mode.COMMAND, profile)
    assert before["system_sha256"] == hashlib.sha256(before["system_prompt"].encode()).hexdigest()
    monkeypatch.setattr(prompts, "COMMON_RULES", prompts.COMMON_RULES + "\nchanged")
    assert prompts.policy_snapshot(Mode.COMMAND, profile)["system_sha256"] != before["system_sha256"]


def test_effective_policy_matches_reviewed_version_snapshot():
    expected = qa.read(qa.ROOT / "tests/fixtures/policy_hashes.json")
    assert {key: {field: value[field] for field in ("policy_version", "profile_version", "system_sha256")}
            for key, value in qa.policies().items()} == expected


def test_seed_keeps_original_failure_and_only_seventeen_missing(tmp_path):
    original = {p: p.read_bytes() for p in qa.LEGACY.glob("*") if p.is_file()}
    manifest = prepare(tmp_path, seed=True)
    records = qa.records(tmp_path / "batch", manifest)
    assert len(records) == 7
    assert len(qa.pending(manifest, records)) == 17
    assert ("C08", "Astra", 1) not in qa.pending(manifest, records)
    c08 = records[("C08", "Astra", 1)]
    assert "成果優先" in c08["output"]
    assert c08["origin"] == "legacy-gui"
    assert all(p.read_bytes() == content for p, content in original.items())
    report = qa.render_report(manifest, records)
    assert c08["output"] in report
    assert "severe_errors" in report and "人工" in report


def test_batch_is_exclusive_and_three_repeats_cannot_seed_ornith(tmp_path):
    prepare(tmp_path)
    with pytest.raises(FileExistsError):
        prepare(tmp_path)
    with pytest.raises(ValueError):
        qa.prepare(tmp_path / "other", "http://127.0.0.1:8080/v1", qa.ORNITH_MODEL,
                   qa.ORNITH_VERSION, 60, 3, True)


def test_dry_plan_has_no_calls_or_outputs(tmp_path, capsys):
    assert qa.main(["plan"]) == 0
    assert "24" in capsys.readouterr().out
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("failure", [False, True])
def test_request_reserved_before_send_and_never_repeated(tmp_path, failure):
    manifest = prepare(tmp_path)
    batch = tmp_path / "batch"
    calls = []

    def respond(request):
        saved = qa.records(batch, manifest)
        assert saved[("C01", "Astra", 1)]["state"] == "started"
        payload = json.loads(request.content)
        assert set(payload) == {"model", "stream", "messages"}
        assert payload["messages"][1]["content"] == manifest["cases"][0]["input"]
        calls.append(payload)
        if failure:
            raise httpx.ReadTimeout("secret must not be saved", request=request)
        return httpx.Response(200, json={"model": "reported-test", "choices": [
            {"finish_reason": "stop", "message": {"content": " raw output\n"}}]})

    qa.run(batch, limit=1, transport=httpx.MockTransport(respond))
    saved = qa.records(batch, manifest)[("C01", "Astra", 1)]
    assert len(calls) == 1
    assert saved["state"] == ("error" if failure else "complete")
    assert "secret must not" not in json.dumps(saved)
    assert saved["output"] == (None if failure else " raw output\n")
    assert saved["actual_model"] == (None if failure else "reported-test")
    assert ("C01", "Astra", 1) not in qa.pending(manifest, qa.records(batch, manifest))
    assert len(qa.pending(manifest, qa.records(batch, manifest))) == 23


def test_interrupted_attempt_is_not_resent(tmp_path):
    manifest = prepare(tmp_path)

    def interrupt(request):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        qa.run(tmp_path / "batch", limit=1, transport=httpx.MockTransport(interrupt))
    saved = qa.records(tmp_path / "batch", manifest)
    assert saved[("C01", "Astra", 1)]["state"] == "started"
    assert len(qa.pending(manifest, saved)) == 23


def test_resume_rejects_policy_change_before_network(tmp_path, monkeypatch):
    prepare(tmp_path)
    monkeypatch.setattr(prompts, "COMMON_RULES", "changed")
    with pytest.raises(ValueError, match="policy"):
        qa.run(tmp_path / "batch", limit=1)


def test_three_repeat_manifest_does_not_send_requests(tmp_path):
    manifest = prepare(tmp_path, repeats=3)
    assert len(qa.pending(manifest, {})) == 72
    assert qa.records(tmp_path / "batch", manifest) == {}


def test_resume_sends_only_next_missing_cell_and_keeps_secret_out(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_COACH_API_KEY", "synthetic-test-key")
    manifest = prepare(tmp_path)
    calls = []

    def respond(request):
        assert request.headers["Authorization"] == "Bearer synthetic-test-key"
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "result"}}]})

    for _ in range(2):
        qa.run(tmp_path / "batch", limit=1, transport=httpx.MockTransport(respond))
    saved = qa.records(tmp_path / "batch", manifest)
    assert set(saved) == {("C01", "Astra", 1), ("C01", "Generic", 1)}
    assert len(calls) == 2
    assert all(r["actual_model"] is None for r in saved.values())
    assert all("synthetic-test-key" not in p.read_text(encoding="utf-8")
               for p in (tmp_path / "batch").rglob("*.json"))


def test_operational_error_stops_batch_without_using_remaining_budget(tmp_path):
    manifest = prepare(tmp_path)
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(429, text="private error body")

    assert qa.run(tmp_path / "batch", limit=24, transport=httpx.MockTransport(respond)) == 1
    assert len(calls) == 1
    saved = qa.records(tmp_path / "batch", manifest)
    assert next(iter(saved.values()))["error_code"] == "rate_limit"
    assert "private error body" not in json.dumps(list(saved.values()))


def test_report_does_not_overwrite_human_review(tmp_path):
    prepare(tmp_path)
    output = tmp_path / "review.md"
    output.write_text("human review", encoding="utf-8")
    with pytest.raises(SystemExit):
        qa.main(["report", "--batch", str(tmp_path / "batch"), "--output", str(output)])
    assert output.read_text(encoding="utf-8") == "human review"


def test_published_coverage_keeps_all_attempts_and_original_c08():
    batch = qa.ROOT / "docs/acceptance/evidence/ornith-coverage"
    manifest = qa.read(batch / "manifest.json")
    saved = qa.records(batch, manifest)
    assert len(saved) == 24 and not qa.pending(manifest, saved)
    assert {key[2] for key in saved} == {1}
    assert sum(row["origin"] == "legacy-gui" for row in saved.values()) == 7
    assert sum(row["origin"] == "headless-product-client" for row in saved.values()) == 17
    assert sum(row["state"] == "complete" for row in saved.values()) == 23
    failed = saved[("C10", "Generic", 1)]
    assert failed["state"] == "error" and failed["error_code"] == "timeout"
    assert failed["output"] is None and failed["actual_model"] is None
    original = qa.read(qa.LEGACY / "representative-runs.json")[0]
    assert saved[("C08", "Astra", 1)]["output"] == original["text"]
    cases = {c["id"]: c for c in manifest["cases"]}
    for key, row in saved.items():
        assert row["request"] == qa.body_for(manifest, cases[key[0]], key[1])
        assert not any(row["human_review"].values())
        if row["state"] == "complete":
            assert row["http"]["status"] == 200 and row["http"]["finish_reason"] == "stop"
            assert row["output"].strip()
