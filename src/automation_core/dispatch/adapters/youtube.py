from __future__ import annotations

from typing import Any


class YoutubeAdapter:
    name = "youtube"

    def supports(self, target: str, platform: str) -> bool:
        return target == "youtube" and platform == "youtube"

    def build_actions(
        self,
        *,
        short_bytes: int,
        long_bytes: int,
        publish_reason: str,
        target: str,
    ) -> list[dict[str, Any]]:
        short_b = short_bytes if short_bytes >= 0 else 0
        long_b = long_bytes if long_bytes >= 0 else 0
        return [
            {
                "type": "print",
                "label": "short",
                "bytes": short_b,
                "adapter": self.name,
                "target": target,
            },
            {
                "type": "print",
                "label": "long",
                "bytes": long_b,
                "adapter": self.name,
                "target": target,
            },
            {
                "type": "noop",
                "label": "publish",
                "reason": publish_reason,
                "adapter": self.name,
                "target": target,
            },
        ]
