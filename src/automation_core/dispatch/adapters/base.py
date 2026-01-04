from __future__ import annotations

from typing import Any, Protocol


class DispatchAdapter(Protocol):
    """สัญญา adapter สำหรับวางแผน actions แบบ audit-only"""

    name: str

    def supports(self, target: str, platform: str) -> bool: ...

    def build_actions(
        self,
        *,
        short_bytes: int,
        long_bytes: int,
        publish_reason: str,
        target: str,
    ) -> list[dict[str, Any]]: ...
