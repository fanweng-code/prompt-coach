import json
from pathlib import Path

from prompt_coach.models import Mode


def test_quality_set_has_twelve_complete_unreviewed_cases():
    cases = json.loads((Path(__file__).parent / "fixtures" / "quality_cases.json").read_text(encoding="utf-8"))
    assert len(cases) == 12
    assert {case["id"] for case in cases} == {f"C{i:02d}" for i in range(1, 13)}
    for case in cases:
        assert set(case) == {"id", "input", "mode", "must_preserve", "must_not_add", "execution_allowed", "human_review"}
        assert isinstance(case["input"], str) and case["input"]
        assert case["mode"] in {m.value for m in Mode}
        for key in ("must_preserve", "must_not_add"):
            assert isinstance(case[key], list) and case[key]
            assert all(isinstance(item, str) and item.strip() for item in case[key])
        assert case["execution_allowed"]
        assert case["human_review"] == {"reviewer": "", "verdict": "", "notes": ""}
