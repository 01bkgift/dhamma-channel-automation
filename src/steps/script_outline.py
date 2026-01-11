"""
ScriptOutline Pipeline Step
Wraps ScriptOutlineAgent for orchestrator integration
Supports input_from with original_research schema from data_enrichment.json
"""

import json
import logging
from pathlib import Path
from typing import TypedDict

from agents.script_outline import (
    RetentionGoals,
    ScriptOutlineAgent,
    ScriptOutlineInput,
    StylePreferences,
    ViewerPersona,
)
from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)


# Constants
MAX_SUMMARY_BULLETS = 3
MAX_CORE_CONCEPTS = 5

DEFAULT_TOPIC_TITLE = "หัวข้อทดสอบ"
DEFAULT_VIEWER_NAME = "คนทำงานเมือง"
DEFAULT_PAIN_POINTS = ["เครียดจากงาน"]
DEFAULT_DESIRED_STATE = "ใจสงบ"
DEFAULT_TONE = "อบอุ่น สงบ"
DEFAULT_MIN_CONFIDENCE = 70


class ScriptOutlineContext(TypedDict, total=False):
    """Context for ScriptOutlineStep"""
    # Input from previous step (via input_from in pipeline)
    input_file: str  # Path to data_enrichment.json

    # Direct input (alternative)
    topic_title: str
    summary_bullets: list[str]
    core_concepts: list[str]
    missing_concepts: list[str]
    target_minutes: int

    # Viewer persona
    viewer_name: str
    pain_points: list[str]
    desired_state: str

    # Style preferences
    tone: str
    avoid: list[str]

    # Retention goals
    hook_drop_max_pct: int
    mid_segment_break_every_sec: int

    # Output location
    output_dir: str


class ScriptOutlineStep(BaseStep):
    """Pipeline step for creating video script outlines"""

    def __init__(self):
        super().__init__(
            step_id="script_outline",
            step_type="ScriptOutline",
            version="1.0.0",
        )
        self.agent = ScriptOutlineAgent()

    def execute(self, context: ScriptOutlineContext) -> dict:
        """Execute script outline generation"""
        # Get input data from input_from file or direct context
        input_data = self._get_input_data(context)

        if not input_data:
            return {
                "status": "error",
                "error": "No input data. Provide input_file or direct parameters.",
            }

        # Build agent input
        try:
            agent_input = self._build_agent_input(input_data, context)
        except Exception as e:
            self.logger.error(f"Failed to create agent input: {e}")
            return {"status": "error", "error": f"Invalid input parameters: {e}"}

        # Run agent
        self.logger.info(f"Running ScriptOutline for: {agent_input.topic_title}")
        result = self.agent.run(agent_input)

        # Save output
        output_dir = Path(context.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        json_path = output_dir / "outline.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        # Save as Markdown
        md_path = output_dir / "outline.md"
        md_content = self._generate_markdown(result)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        self.logger.info(
            f"Generated outline with {len(result.outline)} sections, "
            f"total {result.pacing_check.total_est_seconds}s"
        )

        return {
            "status": "success",
            "output_file": str(json_path),
            "markdown_file": str(md_path),
            "topic": result.topic,
            "section_count": len(result.outline),
            "total_seconds": result.pacing_check.total_est_seconds,
            "within_target": result.pacing_check.within_range,
            "coverage_ratio": result.concept_coverage.coverage_ratio,
            "warnings": result.warnings,
        }

    def _extract_research_data(self, data: dict, research_key: str | None = None) -> dict:
        """Helper to extract research data from different formats"""
        source = data.get(research_key, {}) if research_key else data

        # Extract topic, falling back to top-level if needed
        topic = source.get("topic", data.get("topic", ""))

        # Extract claims
        claims = source.get("claims", [])

        # Extract keywords
        keywords = source.get("keywords", [])

        return {
            "topic_title": topic,
            "summary_bullets": [c.get("text", "") for c in claims[:MAX_SUMMARY_BULLETS]],
            "core_concepts": keywords[:MAX_CORE_CONCEPTS],
            "missing_concepts": [],
        }

    def _get_input_data(self, context: ScriptOutlineContext) -> dict | None:
        """Extract input data from context or input_file"""
        # Priority 1: Direct topic_title in context
        if context.get("topic_title"):
            return {
                "topic_title": context.get("topic_title"),
                "summary_bullets": context.get("summary_bullets") or [],
                "core_concepts": context.get("core_concepts") or [],
                "missing_concepts": context.get("missing_concepts") or [],
            }

        # Priority 2: From input_file
        input_file = context.get("input_file")
        if input_file:
            input_path = Path(input_file)
            if input_path.exists():
                try:
                    with open(input_path, encoding="utf-8") as f:
                        data = json.load(f)

                    # Handle data_enrichment.json with original_research
                    if "original_research" in data:
                        return self._extract_research_data(data, "original_research")

                    # Handle research_bundle.json format (direct)
                    if "claims" in data and "topic" in data:
                        return self._extract_research_data(data)

                    # Direct format with topic_title
                    if "topic_title" in data:
                        return data

                except Exception as e:
                    self.logger.warning(f"Failed to read input file {input_path}: {e}")

        return None

    def _build_agent_input(
        self, input_data: dict, context: ScriptOutlineContext
    ) -> ScriptOutlineInput:
        """Build ScriptOutlineInput from input data and context"""
        return ScriptOutlineInput(
            topic_title=input_data.get("topic_title", DEFAULT_TOPIC_TITLE),
            summary_bullets=input_data.get("summary_bullets") or ["สรุปประเด็นหลัก"],
            core_concepts=input_data.get("core_concepts") or ["สติ"],
            missing_concepts=input_data.get("missing_concepts") or [],
            target_minutes=context.get("target_minutes", 10),
            viewer_persona=ViewerPersona(
                name=context.get("viewer_name", DEFAULT_VIEWER_NAME),
                pain_points=context.get("pain_points") or DEFAULT_PAIN_POINTS,
                desired_state=context.get("desired_state", DEFAULT_DESIRED_STATE),
            ),
            style_preferences=StylePreferences(
                tone=context.get("tone", DEFAULT_TONE),
                avoid=context.get("avoid") or [],
            ),
            retention_goals=RetentionGoals(
                hook_drop_max_pct=context.get("hook_drop_max_pct", 30),
                mid_segment_break_every_sec=context.get("mid_segment_break_every_sec", 120),
            ),
        )

    def _generate_markdown(self, result) -> str:
        """Generate markdown from ScriptOutlineOutput"""
        lines = [
            f"# {result.topic}",
            "",
            f"**เป้าหมาย**: {result.duration_target_min} นาที",
            f"**เวลารวม**: {result.pacing_check.total_est_seconds} วินาที",
            "",
            "## โครงร่าง",
            "",
        ]

        for section in result.outline:
            lines.append(f"### {section.section}")
            lines.append(f"*{section.est_seconds} วินาที*")
            if section.goal:
                lines.append(f"**เป้าหมาย**: {section.goal}")
            if section.content_draft:
                lines.append(f"{section.content_draft}")
            if section.key_points:
                lines.append("**ประเด็นสำคัญ**:")
                for point in section.key_points:
                    lines.append(f"- {point}")
            if section.steps:
                lines.append("**ขั้นตอน**:")
                for i, step in enumerate(section.steps, 1):
                    lines.append(f"{i}. {step}")
            if section.question:
                lines.append(f"**คำถาม**: {section.question}")
            lines.append("")

        if result.warnings:
            lines.extend(["## คำเตือน", ""])
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")

        return "\n".join(lines)
