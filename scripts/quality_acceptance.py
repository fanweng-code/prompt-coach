"""Synthetic Task 8 evidence only. No retries, automatic judge, or GUI claims."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import httpx

from prompt_coach.config import resolve_settings
from prompt_coach.llm_client import LLMClient
from prompt_coach.models import AppConfig, Mode, ProfileId, RewriteError
from prompt_coach.profiles import get_profile
from prompt_coach.prompts import policy_snapshot
from prompt_coach.transformer import PromptTransformer

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/fixtures/quality_cases.json"
LEGACY = ROOT / "docs/acceptance/evidence/ornith-seven"
ORNITH_MODEL = "dealignai/Ornith-1.5-9B-CRACK-GGUF:Q6_K"
ORNITH_VERSION = "b10590-6657ded4f"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value, *, exclusive=True):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if exclusive:
        with path.open("x", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
    else:
        # A crash leaves the already reserved attempt, never an invitation to retry.
        temporary = path.with_suffix(".tmp")
        write(temporary, value)
        temporary.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def policies():
    return {f"{mode.value}/{profile.value}": policy_snapshot(mode, get_profile(profile))
            for mode in Mode for profile in ProfileId}


def source_hashes():
    # Normalize checkout line endings for identical Windows/Linux source identity.
    paths = sorted((ROOT / "src/prompt_coach").glob("*.py"))
    paths += [ROOT / "requirements-lock.txt", Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): digest(p.read_text(encoding="utf-8").encode("utf-8"))
            for p in paths}


def git_revision():
    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
            cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def body_for(manifest, case, profile):
    return {"model": manifest["model"], "stream": False, "messages": [
        {"role": "system", "content": manifest["policies"][f'{case["mode"]}/{profile}']["system_prompt"]},
        {"role": "user", "content": case["input"]}]}


def key_for(row):
    return row["case_id"], row["profile_id"], row["run_index"]


def filename(key):
    return f"{key[0]}-{key[1]}-{key[2]}.json"


def pending(manifest, saved):
    return [(case["id"], profile.value, repeat)
            for case in manifest["cases"] for profile in ProfileId
            for repeat in range(1, manifest["repeats"] + 1)
            if (case["id"], profile.value, repeat) not in saved]


def records(batch, manifest):
    result = {}
    for path in sorted((batch / "runs").glob("*.json")):
        row = read(path)
        key = key_for(row)
        if row["manifest_sha256"] != digest(canonical(manifest)) or key not in pending(manifest, {}):
            raise ValueError("record does not belong to this manifest")
        if key in result or path.name != filename(key):
            raise ValueError("duplicate or misnamed record")
        result[key] = row
    return result


def blank_record(manifest, case, profile, repeat):
    return {"case_id": case["id"], "profile_id": profile, "run_index": repeat,
            "manifest_sha256": digest(canonical(manifest)), "origin": "headless-product-client",
            "state": "started", "started_at": now(), "request": body_for(manifest, case, profile),
            "output": None, "actual_model": None, "elapsed_s": None, "error_code": None,
            "http": {}, "human_review": {"reviewer": "", "date": "", "verdict": "",
                                          "severe_errors": None, "notes": ""}}


def legacy_rows(manifest):
    rows, ledger = read(LEGACY / "representative-runs.json"), read(LEGACY / "request-ledger.json")
    expected = {("C08", "Astra"), *( (c, p.value) for c in ("C01", "C03", "C07") for p in ProfileId)}
    if len(rows) != 7 or len(ledger) != 7 or {(r["case_id"], r["profile_id"]) for r in rows} != expected:
        raise ValueError("legacy evidence is not the original seven combinations")
    cases = {c["id"]: c for c in manifest["cases"]}
    normalized = []
    for old, entry in zip(rows, ledger, strict=True):
        case, profile = cases[old["case_id"]], old["profile_id"]
        if (old["input"] != case["input"] or old["mode"] != case["mode"]
                or old["run_index"] != 1 or old["profile_version"] != get_profile(ProfileId(profile)).version
                or old["backend_version"] != manifest["backend_version"]
                or old["requested_model"] != manifest["model"] or old["actual_model"] != manifest["model"]
                or entry["case_id"] != case["id"] or entry["profile"] != profile
                or entry["body"] != body_for(manifest, case, profile)
                or old["http"] != entry["http"] or old["http"]["status"] != 200
                or old["http"]["finish_reason"] != "stop" or not old["text"].strip()):
            raise ValueError("legacy input, policy, backend or request mismatch")
        row = blank_record(manifest, case, profile, 1)
        row.update(origin="legacy-gui", state="complete", started_at=entry["started_at"],
                   finished_at=old["recorded_at"], output=old["text"], actual_model=old["actual_model"],
                   elapsed_s=old["elapsed_s"], http=old["http"],
                   legacy_source=f"docs/acceptance/evidence/ornith-seven/representative-runs.json#{entry['number']}")
        normalized.append(row)
    return normalized


def prepare(batch, base_url, model, backend_version, timeout, repeats=1, seed=False):
    settings = resolve_settings(AppConfig(base_url, model, timeout), "", os.environ)
    if repeats not in (1, 3):
        raise ValueError("repeats must be 1 or 3")
    if seed and (repeats != 1 or model != ORNITH_MODEL or backend_version != ORNITH_VERSION
                 or settings.base_url != "http://127.0.0.1:8080/v1"):
        raise ValueError("legacy seed is only for the original Ornith single-pass coverage")
    manifest = {"schema_version": 1, "created_at": now(), "base_url": settings.base_url,
                "model": model, "backend_version": backend_version,
                "backend_version_source": "operator supplied; verify against running server",
                "read_timeout_s": timeout, "repeats": repeats,
                "purpose": "temporary-coverage" if repeats == 1 else "final-model-qualification",
                "cases": read(CASES), "cases_sha256": digest(canonical(read(CASES))),
                "policies": policies(), "source_sha256": source_hashes(),
                "git_head": git_revision(), "python": platform.python_version(),
                "platform": platform.system(), "httpx": httpx.__version__,
                "sampling": "server defaults; no sampling fields sent; cache/order uncontrolled",
                "legacy_sha256": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes())
                                  for p in sorted(LEGACY.glob("*")) if p.is_file()} if seed else {}}
    imported = legacy_rows(manifest) if seed else []  # Validate before creating anything.
    batch.mkdir(parents=True, exist_ok=False)
    (batch / "runs").mkdir()
    write(batch / "manifest.json", manifest)
    for row in imported:
        write(batch / "runs" / filename(key_for(row)), row)
    return manifest


class CaptureTransport(httpx.BaseTransport):
    def __init__(self, inner, row):
        self.inner, self.row = inner, row

    def handle_request(self, request):
        if json.loads(request.content) != self.row["request"]:
            raise ValueError("actual request differs from saved request")
        response = self.inner.handle_request(request)
        response.read()
        metadata = self.row["http"]
        metadata["status"] = response.status_code
        try:
            data = response.json()
            choice = data.get("choices", [{}])[0]
            metadata.update(finish_reason=choice.get("finish_reason"), usage=data.get("usage"),
                            timings=data.get("timings"))
        except (ValueError, AttributeError, IndexError, TypeError):
            pass  # Product client remains responsible for response validation.
        return response

    def close(self):
        self.inner.close()


def run(batch, *, limit, transport=None):
    if limit < 1:
        raise ValueError("limit must be positive")
    manifest = read(batch / "manifest.json")
    if manifest["policies"] != policies():
        raise ValueError("policy changed; create a separate batch")
    if manifest["source_sha256"] != source_hashes() or manifest["cases_sha256"] != digest(canonical(read(CASES))):
        raise ValueError("source or cases changed; create a separate batch")
    settings = resolve_settings(AppConfig(manifest["base_url"], manifest["model"], manifest["read_timeout_s"]), "", os.environ)
    saved = records(batch, manifest)
    cases = {c["id"]: c for c in manifest["cases"]}
    errors = 0
    for case_id, profile, repeat in pending(manifest, saved)[:limit]:
        case = cases[case_id]
        row = blank_record(manifest, case, profile, repeat)
        path = batch / "runs" / filename((case_id, profile, repeat))
        write(path, row)  # Exclusive reservation before any network request.
        started = time.perf_counter()
        try:
            capture = CaptureTransport(transport if transport is not None else httpx.HTTPTransport(retries=0), row)
            result = PromptTransformer(LLMClient(settings, capture)).rewrite(case["input"], Mode(case["mode"]), ProfileId(profile))
            row.update(state="complete", output=result.text, actual_model=result.actual_model)
        except RewriteError as exc:
            row.update(state="error", error_code=exc.code)
            errors += 1
        row.update(finished_at=now(), elapsed_s=time.perf_counter() - started)
        write(path, row, exclusive=False)
        print(f"{case_id}/{profile}/{repeat}: {row['state']} ({row['elapsed_s']:.2f}s)", flush=True)
        if row["state"] == "error":
            break  # Stop batch on operational failure; never retry this cell.
    return errors


def quote(text):
    return "\n".join("> " + line for line in text.splitlines())


def render_report(manifest, saved):
    total = len(pending(manifest, {}))
    complete = sum(r["state"] == "complete" for r in saved.values())
    parts = ["# Task 8 合成品質評閱表", "",
             f"完整回應 {complete}/{total}；已記錄嘗試 {len(saved)}/{total}。HTTP 完成不代表品質通過。",
             "人工品質待評閱；最終模型 qualification 與 macOS Task 9 仍待驗。",
             "C08/Astra 原失敗如有匯入，必須保留；legacy-gui 與 headless-product-client 分別標示。",
             f"目的地：{manifest['base_url']}；請求模型：{manifest['model']}；後端版本：{manifest['backend_version']}。",
             f"manifest SHA256：`{digest(canonical(manifest))}`；案例 SHA256：`{manifest['cases_sha256']}`。",
             "版本欄為操作者提供；sampling/cache/order 未受控，不能比較 profile 速度或沿用到其他模型。",
             "填寫每項結果與證據；未評閱 severe_errors 留空，不能當作 0。", ""]
    for case in manifest["cases"]:
        parts += [f"## {case['id']} / {case['mode']}", "", "原文：", quote(case["input"]), ""]
        for profile in ProfileId:
            policy = manifest["policies"][f"{case['mode']}/{profile.value}"]
            for repeat in range(1, manifest["repeats"] + 1):
                row = saved.get((case["id"], profile.value, repeat))
                parts += [f"### {profile.value} / {repeat}", "",
                          f"政策 {policy['policy_version']} / profile {policy['profile_version']} / SHA256 `{policy['system_sha256']}`"]
                if row is None:
                    parts += ["未執行。", ""]
                    continue
                parts += [f"狀態：{row['state']}；來源：{row['origin']}；回報模型：{row['actual_model'] or '未回報'}；耗時：{row['elapsed_s']} 秒。",
                          f"錯誤：{row['error_code'] or '無已記錄錯誤'}；紀錄：runs/{filename(key_for(row))}", "",
                          "完整輸出：", quote(row["output"]) if row["output"] is not None else "無完整輸出。", "",
                          "| 類別 | 核對項 | 人工結果 | 證據／說明 |", "|---|---|---|---|"]
                for category in ("must_preserve", "must_not_add"):
                    parts += [f"| {category} | {item.replace('|', '&#124;')} | | |" for item in case[category]]
                parts += [f"| execution_allowed | {case['execution_allowed']} | | |", "",
                          "reviewer：　date：　verdict：", "", "severe_errors（未評閱留空）：", "", "style_notes：", ""]
    return "\n".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Offline plan; no writes or inference")
    plan.add_argument("--batch", type=Path)
    init = sub.add_parser("prepare", help="Create an exclusive evidence batch; no inference")
    init.add_argument("--batch", required=True, type=Path)
    init.add_argument("--base-url", required=True)
    init.add_argument("--model", required=True)
    init.add_argument("--backend-version", default="unreported")
    init.add_argument("--timeout", type=float, default=60)
    init.add_argument("--repeats", type=int, choices=(1, 3), default=1)
    init.add_argument("--seed-ornith-seven", action="store_true")
    execute = sub.add_parser("run", help="Explicit real requests for missing cells only; stops on error")
    execute.add_argument("--batch", type=Path, required=True)
    execute.add_argument("--limit", type=int, required=True)
    report = sub.add_parser("report", help="Offline review sheet; refuses overwrite")
    report.add_argument("--batch", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            manifest = prepare(args.batch, args.base_url, args.model, args.backend_version,
                               args.timeout, args.repeats, args.seed_ornith_seven)
            print(f"Prepared {len(pending(manifest, records(args.batch, manifest)))} missing cells; no inference.")
        elif args.command == "run":
            return 1 if run(args.batch, limit=args.limit) else 0
        elif args.command == "report":
            manifest = read(args.batch / "manifest.json")
            with args.output.open("x", encoding="utf-8", newline="\n") as f:
                f.write(render_report(manifest, records(args.batch, manifest)))
        else:
            manifest = read(args.batch / "manifest.json") if args.batch else {"cases": read(CASES), "repeats": 1}
            saved = records(args.batch, manifest) if args.batch else {}
            missing = pending(manifest, saved)
            print(f"{len(missing)} missing cells; no inference.")
            for key in missing:
                print("/".join(map(str, key)))
    except (ValueError, OSError, KeyError, RewriteError):
        parser.exit(2, "Invalid configuration/evidence or output already exists. No automatic retry.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
