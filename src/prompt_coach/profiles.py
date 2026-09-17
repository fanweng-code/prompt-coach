from dataclasses import dataclass

from .models import ProfileId


@dataclass(frozen=True)
class Profile:
    id: ProfileId
    version: str
    source_references: tuple[str, ...]
    last_reviewed: str
    instructions: str


PROFILES = {
    ProfileId.ASTRA: Profile(
        ProfileId.ASTRA, "1.0.0", ("S01", "S02"), "2026-09-17",
        "輸出對象 Astra：成果優先，保留必要背景，精簡而不失真；不規定例行思考步驟，"
        "不重複相同限制，不堆角色扮演與強調詞。完整保留使用者明確指定的方法、順序及停止條件。"
        "模型判斷空間只存在於已授權範圍內；此 profile 不新增執行授權或要求。",
    ),
    ProfileId.GENERIC: Profile(
        ProfileId.GENERIC, "1.0.0", ("S02", "design §5.2"), "2026-09-17",
        "輸出對象 Generic：本專案保守通用整理策略，遵守同樣的忠實度與權限原則。"
        "複雜任務可加入有用的結構提示，不強制章節、不大量擴寫，不新增要求或權限。"
        "這不是所有模型的已驗證最佳策略。",
    ),
}


def get_profile(profile_id: ProfileId) -> Profile:
    return PROFILES[profile_id]
