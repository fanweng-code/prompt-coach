import json

import httpx
import pytest

from prompt_coach.config import resolve_settings
from prompt_coach.llm_client import LLMClient
from prompt_coach.models import AppConfig, Completion, RewriteError


def response_body(content="整理結果", finish="stop", **extra):
    return {"choices": [{"message": {"content": content}, "finish_reason": finish}], **extra}


def client_with(handler, remote=True, key="synthetic-key"):
    url = "https://example.test/v1/" if remote else "http://127.0.0.1:8000/v1/"
    return LLMClient(resolve_settings(AppConfig(url, "rewrite-model", 17), key, {}), httpx.MockTransport(handler))


def test_one_request_with_only_contract_fields_and_timeout(monkeypatch):
    seen = []
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:9999")

    def handler(request):
        seen.append(request)
        assert str(request.url) == "https://example.test/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer synthetic-key"
        assert json.loads(request.content) == {"model": "rewrite-model", "stream": False,
            "messages": [{"role": "system", "content": "規則"}, {"role": "user", "content": "原文"}]}
        assert request.extensions["timeout"] == {"connect": 5, "read": 17, "write": 60, "pool": 5}
        return httpx.Response(200, json=response_body(model="served-model"))

    client = client_with(handler)
    assert client.complete("規則", "原文") == Completion("整理結果", "served-model")
    assert client.requested_model == "rewrite-model" and len(seen) == 1


@pytest.mark.parametrize("key", ["", "synthetic-local"])
def test_loopback_authorization_only_when_supplied(key):
    def handler(request):
        assert request.headers.get("Authorization") == (f"Bearer {key}" if key else None)
        return httpx.Response(200, json=response_body())
    assert client_with(handler, False, key).complete("規則", "原文").actual_model is None


@pytest.mark.parametrize("status,code", [(401, "auth"), (403, "auth"), (429, "rate_limit"),
    (301, "http"), (302, "http"), (307, "http"), (400, "http"), (500, "http"), (503, "http")])
def test_http_errors_safe_no_redirect_or_retry(status, code):
    seen = []
    def handler(request):
        seen.append(request)
        assert request.url.host == "example.test"
        return httpx.Response(status, text="synthetic-secret", headers={"Location": "https://other.test"})
    with pytest.raises(RewriteError) as error:
        client_with(handler).complete("規則", "原文")
    assert error.value.code == code and "synthetic" not in str(error.value)
    assert len(seen) == 1
    if code == "http":
        assert str(status) in str(error.value)


@pytest.mark.parametrize("exception,code", [(httpx.ConnectTimeout, "timeout"), (httpx.ReadTimeout, "timeout"),
    (httpx.WriteTimeout, "timeout"), (httpx.PoolTimeout, "timeout"), (httpx.ConnectError, "connection"),
    (httpx.ReadError, "connection")])
def test_transport_errors_are_safe_and_not_retried(exception, code):
    seen = []
    def handler(request):
        seen.append(request)
        raise exception("synthetic-key https://private.test", request=request)
    with pytest.raises(RewriteError) as error:
        client_with(handler).complete("規則", "原文")
    assert error.value.code == code and "synthetic" not in str(error.value)
    assert "private" not in str(error.value) and len(seen) == 1


@pytest.mark.parametrize("body", [None, [], {}, {"choices": {}}, {"choices": []}, {"choices": [None]},
    {"choices": [{}]}, {"choices": [{"message": []}]}, response_body(12), response_body(""), response_body(" \n")],
    ids=["null", "array", "missing", "object-choices", "empty-choices", "null-choice", "no-message", "list-message", "number", "empty", "blank"])
def test_invalid_response_shape_is_rejected(body):
    with pytest.raises(RewriteError) as error:
        client_with(lambda r: httpx.Response(200, json=body)).complete("規則", "原文")
    assert error.value.code == "invalid_response"


def test_invalid_json_is_safe():
    with pytest.raises(RewriteError) as error:
        client_with(lambda r: httpx.Response(200, text="synthetic-secret")).complete("規則", "原文")
    assert error.value.code == "invalid_response" and "synthetic" not in str(error.value)


@pytest.mark.parametrize("field", ["reasoning", "reasoning_content", "tool_calls"])
def test_reasoning_or_tools_are_never_used_as_final_text(field):
    body = {"choices": [{"message": {field: "synthetic-private"}, "finish_reason": "stop"}]}
    with pytest.raises(RewriteError) as error:
        client_with(lambda r: httpx.Response(200, json=body)).complete("規則", "原文")
    assert error.value.code == "unsupported_response"


@pytest.mark.parametrize("finish,code", [("length", "truncated"), ("content_filter", "unsupported_response"),
    ("tool_calls", "unsupported_response"), ("function_call", "unsupported_response"), ("unknown", "unsupported_response"),
    ([], "unsupported_response")])
def test_incomplete_finish_never_returns_success(finish, code):
    with pytest.raises(RewriteError) as error:
        client_with(lambda r: httpx.Response(200, json=response_body(finish=finish))).complete("規則", "原文")
    assert error.value.code == code


@pytest.mark.parametrize("finish", ["stop", None, "missing"])
def test_final_text_preserved_and_missing_model_is_not_invented(finish):
    body = response_body("  完整\n文字  ", finish)
    if finish == "missing":
        del body["choices"][0]["finish_reason"]
    assert client_with(lambda r: httpx.Response(200, json=body)).complete("規則", "原文") == Completion("  完整\n文字  ", None)
