"""
Integration tests for DoctrineValidatorStep
Tests validation with realistic script and passages data
Includes ignore_segments and check_sensitive edge cases
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from steps.doctrine_validator import DoctrineValidatorStep


class TestDoctrineValidatorStep:
    """Test suite for DoctrineValidatorStep"""

    def test_step_initialization(self):
        """Test step can be instantiated"""
        step = DoctrineValidatorStep()
        assert step.step_id == "doctrine_validator"
        assert step.step_type == "DoctrineValidator"
        assert step.version == "1.0.0"

    def _generate_valid_script_segments(self) -> list[dict]:
        """Generate valid script segments for testing"""
        return [
            {
                "segment_type": "hook",
                "text": "เคยมีช่วงเวลาที่นอนไม่หลับเพราะความกังวลไหม?",
                "est_seconds": 8,
            },
            {
                "segment_type": "teaching",
                "text": "การมีสติรู้ลมหายใจเข้าออกช่วยให้ใจสงบ [CIT:p123]",
                "est_seconds": 60,
            },
            {
                "segment_type": "practice",
                "text": "ลองหายใจเข้าลึกๆ แล้วหายใจออกช้าๆ",
                "est_seconds": 30,
            },
        ]

    def _generate_valid_passages(self) -> dict:
        """Generate valid passages for testing"""
        return {
            "primary": [
                {
                    "id": "p123",
                    "original_text": "การมีสติรู้ลมหายใจเข้าออกช่วยให้ใจสงบ",
                    "thai_modernized": "การมีสติอยู่กับลมหายใจทำให้ใจสงบ",
                    "doctrinal_tags": ["สติ", "อานาปานสติ"],
                    "canonical_ref": "MN 118",
                    "license": "public_domain",
                }
            ],
            "supportive": [],
        }

    def test_execute_with_direct_input(self, tmp_path):
        """Test with direct script_segments and passages"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert Path(result["output_file"]).exists()
        assert Path(result["report_file"]).exists()
        assert "summary" in result
        assert result["summary"]["total"] == 3

    def test_execute_with_files(self, tmp_path):
        """Test with script_file and passages_file"""
        script_file = tmp_path / "script.json"
        script_data = {
            "topic": "ปล่อยวางความกังวล",
            "segments": self._generate_valid_script_segments(),
        }
        script_file.write_text(
            json.dumps(script_data, ensure_ascii=False),
            encoding="utf-8",
        )

        passages_file = tmp_path / "passages.json"
        passages_file.write_text(
            json.dumps(self._generate_valid_passages(), ensure_ascii=False),
            encoding="utf-8",
        )

        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_file": str(script_file),
                "passages_file": str(passages_file),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert result["summary"]["ok"] >= 1

    def test_output_is_script_validated_md(self, tmp_path):
        """Test output matches video.yaml convention (script_validated.md)"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert result["output_file"].endswith("script_validated.md")

        content = Path(result["output_file"]).read_text(encoding="utf-8")
        assert "<!-- DOCTRINE VALIDATION -->" in content
        assert "APPROVED" in content or "NEEDS_REVIEW" in content

    def test_ignore_segments_filters_correctly(self, tmp_path):
        """Test ignore_segments reduces total count"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "ignore_segments": [0],
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert result["summary"]["total"] == 2

    def test_ignore_all_segments_returns_error(self, tmp_path):
        """Test ignoring all segments returns error (not empty success)"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "ignore_segments": [0, 1, 2],
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "error"
        assert result.get("error_code") == "MISSING_DATA"

    def test_check_sensitive_detects_risky_phrases(self, tmp_path):
        """Test sensitive phrase detection in segment warnings"""
        step = DoctrineValidatorStep()
        segments = [
            {
                "segment_type": "teaching",
                "text": "สมาธิรักษาโรคได้ทุกโรค [CIT:p123]",
                "est_seconds": 30,
            }
        ]

        result = step.execute(
            {
                "script_segments": segments,
                "passages": self._generate_valid_passages(),
                "check_sensitive": True,
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert any("สุ่มเสี่ยง" in w for w in result["warnings"])

    def test_empty_passages_returns_error(self, tmp_path):
        """Test empty passages fails validation"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": {"primary": [], "supportive": []},
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "error"
        assert "passage" in result["error"].lower()

    def test_missing_passages_returns_error(self, tmp_path):
        """Test no passages provided fails"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "error"

    def test_missing_script_error(self, tmp_path):
        """Test error when script segments missing"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "passages": self._generate_valid_passages(),
                "output_dir": str(tmp_path),
            }
        )
        assert result["status"] == "error"

    def test_strictness_modes(self, tmp_path):
        """Test normal vs strict mode"""
        step = DoctrineValidatorStep()

        result_normal = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "strictness": "normal",
                "output_dir": str(tmp_path / "normal"),
            }
        )
        assert result_normal["status"] == "success"

        result_strict = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "strictness": "strict",
                "output_dir": str(tmp_path / "strict"),
            }
        )
        assert result_strict["status"] == "success"

    def test_citation_coverage_in_result(self, tmp_path):
        """Test citation coverage is reported"""
        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages": self._generate_valid_passages(),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert "citation_coverage" in result
        assert "ok_ratio" in result
        assert 0 <= result["citation_coverage"] <= 1
        assert 0 <= result["ok_ratio"] <= 1

    def test_research_bundle_json_format(self, tmp_path):
        """Test with research_bundle.json format from ResearchRetrieval step"""
        research_bundle = {
            "topic": "ปล่อยวางความกังวล",
            "claims": [{"text": "สติช่วยลดความเครียด", "support": "พระไตรปิฎก"}],
            "passages": {
                "primary": [
                    {
                        "id": "p123",
                        "original_text": "การมีสติรู้ลมหายใจช่วยให้ใจสงบ",
                        "thai_modernized": "มีสติอยู่กับลมหายใจทำให้สงบ",
                        "doctrinal_tags": ["สติ"],
                        "canonical_ref": "MN 118",
                        "license": "public_domain",
                    }
                ],
                "supportive": [],
            },
        }
        passages_file = tmp_path / "research_bundle.json"
        passages_file.write_text(
            json.dumps(research_bundle, ensure_ascii=False),
            encoding="utf-8",
        )

        step = DoctrineValidatorStep()
        result = step.execute(
            {
                "script_segments": self._generate_valid_script_segments(),
                "passages_file": str(passages_file),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert result["summary"]["total"] == 3
