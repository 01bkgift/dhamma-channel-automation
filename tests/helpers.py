from __future__ import annotations

from pathlib import Path


def write_post_templates(base_dir: Path) -> None:
    templates_dir = base_dir / "templates" / "post"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "short.md").write_text(
        "{{hook}}\n{{summary}}\n\n{{cta}}\n{{hashtags}}\n", encoding="utf-8"
    )
    (templates_dir / "long.md").write_text(
        "{{title}}\n\n{{hook}}\n\n{{summary}}\n\n{{cta}}\n\n{{hashtags}}\n",
        encoding="utf-8",
    )
