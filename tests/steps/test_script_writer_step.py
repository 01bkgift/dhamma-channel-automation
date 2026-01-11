"""
Integration tests for ScriptWriterStep
Uses ScriptOutlineAgent to generate valid outline (no handcraft)
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.script_outline import (
    RetentionGoals,
    ScriptOutlineAgent,
    ScriptOutlineInput,
    StylePreferences,
    ViewerPersona,
)
from steps.script_writer import ScriptWriterStep


class TestScriptWriterStep:
    """Test suite for ScriptWriterStep"""

    def test_step_initialization(self):
        """Test step instantiation"""
        step = ScriptWriterStep()
        assert step.step_id == "script_writer"
        assert step.step_type == "ScriptWriter"
        assert step.version == "1.0.0"

    def _generate_valid_outline(self) -> dict:
        """Generate valid outline using ScriptOutlineAgent (not handcraft)"""
        agent = ScriptOutlineAgent()
        input_data = ScriptOutlineInput(
            topic_title="ปล่อยวางความกังวล",
            summary_bullets=["การสังเกตเวทนาโดยไม่ยึด", "อานาปานสติช่วยลดการวนคิด"],
            core_concepts=["สติ", "เวทนา"],
            target_minutes=10,
            viewer_persona=ViewerPersona(
                name="คนทำงานเมือง",
                pain_points=["นอนไม่หลับ"],
                desired_state="ใจสงบ",
            ),
            style_preferences=StylePreferences(
                tone="อบอุ่น สงบ",
                avoid=["ศัพท์บาลี"],
            ),
            retention_goals=RetentionGoals(
                hook_drop_max_pct=30,
                mid_segment_break_every_sec=120,
            ),
        )
        return agent.run(input_data).model_dump()

    def _generate_valid_passages(self) -> dict:
        """Generate valid passages"""
        return {
            "primary": [
                {
                    "id": "p123",
                    "source_name": "อานาปานสติสูตร",
                    "collection": "พระสุตตันตปิฎก",
                    "canonical_ref": "MN 118",
                    "original_text": "อานาปานสติ...",
                    "thai_modernized": "การดูลมหายใจ",
                    "relevance_final": 0.9,
                    "doctrinal_tags": ["สติ"],
                    "license": "public_domain",
                    "reason": "เกี่ยวข้อง",
                }
            ],
            "supportive": [],
        }

    def test_execute_with_files(self, tmp_path):
        """Test with outline and passages files"""
        outline_file = tmp_path / "outline.json"
        outline_file.write_text(
            json.dumps(self._generate_valid_outline(), ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        passages_file = tmp_path / "passages.json"
        passages_file.write_text(
            json.dumps(self._generate_valid_passages(), ensure_ascii=False),
            encoding="utf-8",
        )

        step = ScriptWriterStep()
        result = step.execute({
            "outline_file": str(outline_file),
            "passages_file": str(passages_file),
            "output_dir": str(tmp_path),
        })

        assert result["status"] == "success"
        assert Path(result["output_file"]).exists()
        assert Path(result["script_file"]).exists()
        assert result["segment_count"] > 0

    def test_execute_with_direct_input(self, tmp_path):
        """Test with inline data"""
        step = ScriptWriterStep()
        result = step.execute({
            "outline": self._generate_valid_outline(),
            "passages": self._generate_valid_passages(),
            "output_dir": str(tmp_path),
        })

        assert result["status"] == "success"
        assert "quality_check" in result

    def test_output_is_markdown(self, tmp_path):
        """Test output is script.md (matches video.yaml)"""
        step = ScriptWriterStep()
        result = step.execute({
            "outline": self._generate_valid_outline(),
            "passages": self._generate_valid_passages(),
            "output_dir": str(tmp_path),
        })

        assert result["status"] == "success"
        assert result["script_file"].endswith("script.md")

        md_content = Path(result["script_file"]).read_text(encoding="utf-8")
        assert "# " in md_content
        assert "## [" in md_content

    def test_missing_outline_error(self, tmp_path):
        """Test error when outline missing"""
        step = ScriptWriterStep()
        result = step.execute({
            "passages": self._generate_valid_passages(),
            "output_dir": str(tmp_path),
        })
        assert result["status"] == "error"

    def test_missing_passages_error(self, tmp_path):
        """Test error when passages missing"""
        step = ScriptWriterStep()
        result = step.execute({
            "outline": self._generate_valid_outline(),
            "output_dir": str(tmp_path),
        })
        assert result["status"] == "error"

    def test_quality_check_in_result(self, tmp_path):
        """Test quality check structure"""
        step = ScriptWriterStep()
        result = step.execute({
            "outline": self._generate_valid_outline(),
            "passages": self._generate_valid_passages(),
            "output_dir": str(tmp_path),
        })

        assert result["status"] == "success"
        qc = result["quality_check"]
        assert "citations_valid" in qc
        assert "teaching_has_citation" in qc
        assert "hook_within_8s" in qc
