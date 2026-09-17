import time
from typing import Protocol

from .models import Completion, Mode, ProfileId, RewriteError, RewriteResult
from .profiles import get_profile
from .prompts import build_system_prompt


class RewriteClient(Protocol):
    @property
    def requested_model(self) -> str: ...

    def complete(self, system: str, user: str) -> Completion: ...


class PromptTransformer:
    def __init__(self, client: RewriteClient):
        self.client = client

    def rewrite(self, text: str, mode: Mode, target_profile: ProfileId) -> RewriteResult:
        if not text.strip() or len(text) > 20_000:
            raise RewriteError("input")
        profile = get_profile(target_profile)
        started = time.perf_counter()
        completion = self.client.complete(build_system_prompt(mode, profile), text)
        return RewriteResult(
            text=completion.text, mode=mode, profile_id=profile.id,
            profile_version=profile.version, requested_model=self.client.requested_model,
            actual_model=completion.actual_model, elapsed_s=time.perf_counter() - started,
        )
