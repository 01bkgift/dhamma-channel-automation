"""
ScriptWriter Pipeline Step
- Wraps ScriptWriterAgent for orchestrator integration
- Supports input_from with outline.json from script_outline step
- Outputs script.md (human) + script.json (machine)
"""

import json
import logging
from pathlib import Path
from typing import Optional, TypedDict, Union

from agents.research_retrieval.model import Passage
from agents.script_outline.model import ScriptOutlineOutput
from agents.script_writer import (
    PassageData,
    ScriptWriterAgent,
    ScriptWriterInput,
    StyleNotes,
)
from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TARGET_SECONDS = 600
DEFAULT_TONE = "อบอุ่น สงบ ไม่สั่งสอน"
DEFAULT_VOICE = "เป็นกันเอง สุภาพ ใช้คำว่า เรา/คุณ"


class ScriptWriterContext(TypedDict, total=False):
    """Context for ScriptWriterStep"""
    outline_file: str      # Path to outline.json
    passages_file: str     # Path to passages.json
    outline: dict          # Direct outline data
    passages: dict         # Direct passages data
    tone: str
    voice: str
    avoid: list[str]
    target_seconds: int
    language: str
    output_dir: str


class ScriptWriterStep(BaseStep):
    """Pipeline step for generating video scripts"""

    def __init__(self):
        super().__init__(
            step_id="script_writer",
            step_type="ScriptWriter",
            version="1.0.0",
        )
        self.agent = ScriptWriterAgent()

    def execute(self, context: ScriptWriterContext) -> dict:
        """Execute script writing"""
        outline_data = self._get_outline_data(context)
        if not outline_data:
            return {"status": "error", "error": "No outline data"}

        passages_data = self._get_passages_data(context)
        if not passages_data:
            return {"status": "error", "error": "No passages data"}

        try:
            agent_input = self._build_agent_input(outline_data, passages_data, context)
        except Exception as e:
            self.logger.error(f"Failed to build input: {e}")
            return {"status": "error", "error": str(e)}

        self.logger.info(f"Running ScriptWriter for: {agent_input.outline.topic}")
        result = self.agent.run(agent_input)

        # Save outputs
        output_dir = Path(context.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        # script.json (machine output)
        json_path = output_dir / "script.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        # script.md (human readable - matches video.yaml convention)
        md_path = output_dir / "script.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._generate_markdown(result))

        return {
            "status": "success",
            "output_file": str(json_path),
            "script_file": str(md_path),
            "topic": result.topic,
            "segment_count": len(result.segments),
            "duration_seconds": result.duration_est_total,
            "citations_used": len(result.citations_used),
            "quality_check": result.quality_check.model_dump(),
            "warnings": result.warnings,
        }

    def _get_outline_data(self, context: ScriptWriterContext) -> Optional[ScriptOutlineOutput]:
        """Get outline from file or context"""
        outline_file = context.get("outline_file")
        if outline_file:
            path = Path(outline_file)
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        return ScriptOutlineOutput(**json.load(f))
                except Exception as e:
                    self.logger.warning(f"Failed to load outline: {e}")

        outline = context.get("outline")
        if outline and isinstance(outline, dict):
            try:
                return ScriptOutlineOutput(**outline)
            except Exception as e:
                self.logger.warning(f"Failed to parse outline: {e}")
        return None

    def _get_passages_data(self, context: ScriptWriterContext) -> Optional[PassageData]:
        """Get passages from file or context"""
        passages_file = context.get("passages_file")
        if passages_file:
            path = Path(passages_file)
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        return self._parse_passages(json.load(f))
                except Exception as e:
                    self.logger.warning(f"Failed to load passages: {e}")

        passages = context.get("passages")
        if passages:
            return self._parse_passages(passages)
        return None

    def _parse_passages(self, data: Union[dict, list]) -> PassageData:
        """Parse passages from dict"""
        primary, supportive = [], []
        if isinstance(data, dict):
            for p in data.get("primary", []):
                primary.append(Passage(**p) if isinstance(p, dict) else p)
            for p in data.get("supportive", []):
                supportive.append(Passage(**p) if isinstance(p, dict) else p)
        return PassageData(primary=primary, supportive=supportive)

    def _build_agent_input(
        self, outline: ScriptOutlineOutput, passages: PassageData, context: ScriptWriterContext
    ) -> ScriptWriterInput:
        """Build agent input"""
        return ScriptWriterInput(
            outline=outline,
            passages=passages,
            style_notes=StyleNotes(
                tone=context.get("tone", DEFAULT_TONE),
                voice=context.get("voice", DEFAULT_VOICE),
                avoid=context.get("avoid", []),
            ),
            target_seconds=context.get("target_seconds", DEFAULT_TARGET_SECONDS),
            language=context.get("language", "th"),
        )

    def _generate_markdown(self, result) -> str:
        """Generate markdown script (matches video.yaml output: script.md)"""
        lines = [
            f"# {result.topic}",
            "",
            f"**ความยาว**: {result.duration_est_total} วินาที ({result.duration_est_total / 60:.1f} นาที)",
            "",
            "---",
            "",
        ]
        for seg in result.segments:
            lines.append(f"## [{seg.segment_type.value.upper()}] ({seg.est_seconds}s)")
            lines.append("")
            lines.append(seg.text)
            lines.append("")

        if result.citations_used:
            lines.extend(["---", "", "## อ้างอิง", ""])
            for cit in result.citations_used:
                lines.append(f"- {cit}")

        return "\n".join(lines)
