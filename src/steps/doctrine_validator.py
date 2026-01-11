"""
DoctrineValidator Pipeline Step
- Wraps DoctrineValidatorAgent for orchestrator integration
- Supports input_from with script.md or script.json from ScriptWriter
- Outputs script_validated.md (pass-through + validation header)
- Also outputs validation_report.json for detailed results
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TypedDict

from agents.doctrine_validator import DoctrineValidatorAgent
from agents.doctrine_validator.model import (
    DoctrineValidatorInput,
    DoctrineValidatorOutput,
    ErrorResponse,
    Passage,
    Passages,
    ScriptSegment,
)
from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)

# Constants
DEFAULT_STRICTNESS = "normal"
MIN_PASSAGES_REQUIRED = 1
SEGMENT_HEADER_PATTERN = re.compile(r"^##\s*\[([^\]]+)\](?:\s*\((\d+)s\))?", re.M)


class DoctrineValidatorContext(TypedDict, total=False):
    """Context for DoctrineValidatorStep"""

    # Input files (from previous steps)
    script_file: str  # Path to script.md or script.json from ScriptWriter
    passages_file: str  # Path to research_bundle.json or passages.json

    # Direct input (alternative)
    script_segments: list[dict]
    passages: dict

    # Validation settings
    strictness: str  # "normal" or "strict"
    check_sensitive: bool
    ignore_segments: list[int]

    # Output location
    output_dir: str


class DoctrineValidatorStep(BaseStep):
    """Pipeline step for validating script doctrinal integrity"""

    def __init__(self):
        super().__init__(
            step_id="doctrine_validator",
            step_type="DoctrineValidator",
            version="1.0.0",
        )
        self.agent = DoctrineValidatorAgent()

    def execute(self, context: DoctrineValidatorContext) -> dict:
        """Execute doctrinal validation"""
        original_script, script_segments = self._get_script_data(context)
        if not script_segments:
            return {"status": "error", "error": "No script segments found"}

        passages = self._get_passages(context)
        if not passages:
            return {"status": "error", "error": "No passages found for validation"}

        if not passages.primary and not passages.supportive:
            return {
                "status": "error",
                "error": "Passages must have at least one primary or supportive entry",
            }

        try:
            agent_input = DoctrineValidatorInput(
                script_segments=script_segments,
                passages=passages,
                strictness=context.get("strictness", DEFAULT_STRICTNESS),
                check_sensitive=context.get("check_sensitive", False),
                ignore_segments=context.get("ignore_segments", []),
            )
        except Exception as e:
            self.logger.error(f"Failed to create agent input: {e}")
            return {"status": "error", "error": str(e)}

        self.logger.info(f"Validating {len(script_segments)} segments")
        result = self.agent.run(agent_input)

        if isinstance(result, ErrorResponse):
            return {
                "status": "error",
                "error": result.error.get("message", "Unknown error"),
                "error_code": result.error.get("code"),
            }

        output_dir = Path(context.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        report_json_path = output_dir / "validation_report.json"
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(
                result.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

        validated_script_path = output_dir / "script_validated.md"
        validated_content = self._create_validated_script(original_script, result)
        with open(validated_script_path, "w", encoding="utf-8") as f:
            f.write(validated_content)

        all_warnings = list(result.warnings)
        for seg in result.segments:
            for warn in seg.warnings:
                all_warnings.append(f"[Segment {seg.index}] {warn}")

        return {
            "status": "success",
            "output_file": str(validated_script_path),
            "report_file": str(report_json_path),
            "summary": {
                "total": result.summary.total,
                "ok": result.summary.ok,
                "mismatch": result.summary.mismatch,
                "hallucination": result.summary.hallucination,
                "unclear": result.summary.unclear,
                "missing_citation": result.summary.missing_citation,
                "unverifiable": result.summary.unverifiable,
            },
            "recommend_rewrite": result.summary.recommend_rewrite,
            "ok_ratio": result.meta.self_check.ok_ratio,
            "citation_coverage": result.meta.citation_coverage,
            "warnings": all_warnings,
        }

    def _get_script_data(
        self, context: DoctrineValidatorContext
    ) -> tuple[str, list[ScriptSegment] | None]:
        """Get original script content and segments"""
        original_script = ""

        direct_segments = context.get("script_segments")
        if direct_segments:
            try:
                segments: list[ScriptSegment] = []
                for raw in direct_segments:
                    if isinstance(raw, ScriptSegment):
                        segments.append(raw)
                        continue
                    if not isinstance(raw, dict):
                        raise TypeError("script_segments entries must be dict-like")
                    segment_type = raw.get("segment_type", "teaching")
                    if hasattr(segment_type, "value"):
                        segment_type = segment_type.value
                    segments.append(
                        ScriptSegment(
                            segment_type=segment_type,
                            text=raw.get("text", ""),
                            est_seconds=raw.get("est_seconds"),
                        )
                    )
                original_script = "\n\n".join(s.text for s in segments if s.text)
                return original_script, segments
            except Exception as e:
                self.logger.warning(f"Failed to parse direct segments: {e}")

        script_file = context.get("script_file")
        if script_file:
            path = Path(script_file)
            if path.exists():
                try:
                    original_script = path.read_text(encoding="utf-8")
                    if path.suffix.lower() == ".json":
                        data = json.loads(original_script)
                        if "segments" in data:
                            segments = []
                            for raw in data["segments"]:
                                segment_type = raw.get("segment_type", "teaching")
                                if hasattr(segment_type, "value"):
                                    segment_type = segment_type.value
                                segments.append(
                                    ScriptSegment(
                                        segment_type=segment_type,
                                        text=raw.get("text", ""),
                                        est_seconds=raw.get("est_seconds"),
                                    )
                                )
                            md_path = path.with_suffix(".md")
                            if md_path.exists():
                                try:
                                    original_script = md_path.read_text(
                                        encoding="utf-8"
                                    )
                                except Exception as e:
                                    self.logger.warning(
                                        f"Failed to load markdown script: {e}"
                                    )
                            else:
                                original_script = "\n\n".join(
                                    s.text for s in segments if s.text
                                )
                            return original_script, segments

                    segments = self._parse_markdown_to_segments(original_script)
                    return original_script, segments
                except Exception as e:
                    self.logger.warning(f"Failed to load script file: {e}")

        return original_script, None

    def _parse_markdown_to_segments(self, markdown: str) -> list[ScriptSegment]:
        """Parse markdown script into segments (simplified)"""
        segments: list[ScriptSegment] = []
        matches = list(SEGMENT_HEADER_PATTERN.finditer(markdown))
        if matches:
            for idx, match in enumerate(matches):
                start = match.end()
                end = (
                    matches[idx + 1].start()
                    if idx + 1 < len(matches)
                    else len(markdown)
                )
                block = markdown[start:end].strip()
                if not block:
                    continue
                block = block.split("\n## อ้างอิง", 1)[0].strip()
                if not block:
                    continue
                segment_type = match.group(1).strip().lower()
                est_seconds = (
                    int(match.group(2))
                    if match.group(2) and match.group(2).isdigit()
                    else None
                )
                segments.append(
                    ScriptSegment(
                        segment_type=segment_type,
                        text=block,
                        est_seconds=est_seconds,
                    )
                )
            if segments:
                return segments

        blocks = [
            part.strip() for part in markdown.strip().split("\n\n") if part.strip()
        ]
        for i, block in enumerate(blocks[:10]):
            segment_type = "hook" if i == 0 else "teaching"
            segments.append(
                ScriptSegment(
                    segment_type=segment_type,
                    text=block[:500],
                    est_seconds=30,
                )
            )

        if not segments and markdown.strip():
            segments.append(
                ScriptSegment(
                    segment_type="teaching",
                    text=markdown.strip()[:500],
                    est_seconds=60,
                )
            )
        return segments

    def _get_passages(self, context: DoctrineValidatorContext) -> Passages | None:
        """Get passages from file or context"""
        direct_passages = context.get("passages")
        if direct_passages:
            try:
                return self._parse_passages(direct_passages)
            except Exception as e:
                self.logger.warning(f"Failed to parse direct passages: {e}")

        passages_file = context.get("passages_file")
        if passages_file:
            path = Path(passages_file)
            if path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    return self._parse_passages(data)
                except Exception as e:
                    self.logger.warning(f"Failed to load passages file: {e}")

        return None

    def _parse_passages(self, data: dict | Passages) -> Passages | None:
        """Parse passages from dict - returns None if completely empty"""
        if isinstance(data, Passages):
            return data

        primary: list[Passage] = []
        supportive: list[Passage] = []

        if "primary" in data or "supportive" in data:
            for p in data.get("primary", []):
                primary.append(Passage(**p) if isinstance(p, dict) else p)
            for p in data.get("supportive", []):
                supportive.append(Passage(**p) if isinstance(p, dict) else p)
        elif "passages" in data and isinstance(data.get("passages"), dict):
            passages_data = data["passages"]
            for p in passages_data.get("primary", []):
                primary.append(Passage(**p) if isinstance(p, dict) else p)
            for p in passages_data.get("supportive", []):
                supportive.append(Passage(**p) if isinstance(p, dict) else p)

        if len(primary) + len(supportive) < MIN_PASSAGES_REQUIRED:
            return None

        return Passages(primary=primary, supportive=supportive)

    def _create_validated_script(
        self, original_script: str, result: DoctrineValidatorOutput
    ) -> str:
        """Create validated script with validation header (pass-through pattern)"""
        status_emoji = "✅" if result.summary.ok == result.summary.total else "⚠️"
        if result.summary.hallucination > 0 or result.summary.mismatch > 0:
            status_emoji = "❌"

        header = f"""<!-- DOCTRINE VALIDATION -->
<!-- Status: {status_emoji} {"APPROVED" if not result.summary.recommend_rewrite else "NEEDS_REVIEW"} -->
<!-- Validated at: {result.validated_at} -->
<!-- Strictness: {result.strictness} -->
<!-- Summary: OK={result.summary.ok}/{result.summary.total}, Citation Coverage={result.meta.citation_coverage:.0%} -->
<!-- OK Ratio: {result.meta.self_check.ok_ratio:.0%} -->
<!-- ==================== -->

"""

        footer = f"""

<!-- ==================== -->
<!-- VALIDATION SUMMARY -->
<!-- Total: {result.summary.total} | OK: {result.summary.ok} | Mismatch: {result.summary.mismatch} | Hallucination: {result.summary.hallucination} -->
<!-- Recommend Rewrite: {"Yes" if result.summary.recommend_rewrite else "No"} -->
<!-- ==================== -->
"""

        return header + original_script + footer
