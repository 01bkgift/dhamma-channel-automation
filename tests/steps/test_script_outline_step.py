"""
Integration tests for ScriptOutlineStep
Test required sections exist (not count), handle optional sections properly
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from steps.script_outline import ScriptOutlineStep


class TestScriptOutlineStep:
    """Test suite for ScriptOutlineStep"""
    
    REQUIRED_SECTIONS = {"Hook", "Core Teaching", "Practice / Application"}
    
    def test_step_initialization(self):
        """Test step can be instantiated"""
        step = ScriptOutlineStep()
        assert step.step_id == "script_outline"
        assert step.step_type == "ScriptOutline"
        assert step.version == "1.0.0"
    
    def test_execute_with_direct_input(self, tmp_path):
        """Test execution with direct input parameters"""
        step = ScriptOutlineStep()
        result = step.execute({
            "topic_title": "ปล่อยวางความกังวลก่อนนอน",
            "summary_bullets": [
                "การสังเกตเวทนาโดยไม่ยึดช่วยคลายกังวล",
                "อานาปานสติช่วงสั้นก่อนหลับลดการวนคิด",
            ],
            "core_concepts": ["สติ", "เวทนา", "ปล่อยวาง"],
            "target_minutes": 10,
            "viewer_name": "คนทำงานเมือง",
            "pain_points": ["นอนไม่ค่อยหลับ", "คิดเรื่องงานซ้ำ"],
            "desired_state": "ใจผ่อนคลาย หลับง่ายขึ้น",
            "output_dir": str(tmp_path),
        })
        
        assert result["status"] == "success"
        assert Path(result["output_file"]).exists()
        assert Path(result["markdown_file"]).exists()
        
        # Check required sections exist
        with open(result["output_file"], encoding="utf-8") as f:
            output = json.load(f)
        sections = {s["section"] for s in output["outline"]}
        assert self.REQUIRED_SECTIONS.issubset(sections)
    
    def test_execute_with_data_enrichment_file(self, tmp_path):
        """Test with data_enrichment.json (original_research schema)"""
        # Create mock data_enrichment.json with original_research
        mock_data = {
            "enriched_at": "2025-01-10T10:00:00",
            "topic": "สมาธิภาวนา",
            "original_research": {
                "topic": "สมาธิภาวนา",
                "claims": [
                    {"text": "สมาธิช่วยลดความเครียด", "support": "พระไตรปิฎก"},
                    {"text": "ฝึกสั้นแต่สม่ำเสมอดีกว่า", "support": "หลวงปู่มั่น"},
                ],
                "keywords": ["สมาธิ", "สติ", "ภาวนา"],
            }
        }
        
        input_file = tmp_path / "data_enrichment.json"
        input_file.write_text(json.dumps(mock_data, ensure_ascii=False), encoding="utf-8")
        
        step = ScriptOutlineStep()
        result = step.execute({
            "input_file": str(input_file),
            "output_dir": str(tmp_path),
        })
        
        assert result["status"] == "success"
        assert result["topic"] == "สมาธิภาวนา"
        
        # Check required sections
        with open(result["output_file"], encoding="utf-8") as f:
            output = json.load(f)
        sections = {s["section"] for s in output["outline"]}
        assert self.REQUIRED_SECTIONS.issubset(sections)
    
    def test_output_structure(self, tmp_path):
        """Test output JSON structure matches schema"""
        step = ScriptOutlineStep()
        result = step.execute({
            "topic_title": "สมาธิภาวนา",
            "summary_bullets": ["หลักการนั่งสมาธิ"],
            "core_concepts": ["สมาธิ", "สติ"],
            "output_dir": str(tmp_path),
        })
        
        assert result["status"] == "success"
        
        with open(result["output_file"], encoding="utf-8") as f:
            output = json.load(f)
        
        assert "topic" in output
        assert "outline" in output
        assert "pacing_check" in output
        assert "concept_coverage" in output
    
    def test_deterministic_output(self, tmp_path):
        """Test same input produces same output (hash determinism)"""
        step = ScriptOutlineStep()
        config = {
            "topic_title": "ทดสอบ determinism",
            "summary_bullets": ["ทดสอบ"],
            "core_concepts": ["สติ"],
            "output_dir": str(tmp_path),
        }
        
        result1 = step.execute(config)
        result2 = step.execute(config)
        
        with open(result1["output_file"], encoding="utf-8") as f:
            output1 = json.load(f)
        with open(result2["output_file"], encoding="utf-8") as f:
            output2 = json.load(f)
        
        # Hook pattern should be identical
        hook1 = next(s for s in output1["outline"] if s["section"] == "Hook")
        hook2 = next(s for s in output2["outline"] if s["section"] == "Hook")
        assert hook1["hook_pattern"] == hook2["hook_pattern"]
    
    def test_missing_input_error(self, tmp_path):
        """Test error handling for missing input"""
        step = ScriptOutlineStep()
        result = step.execute({"output_dir": str(tmp_path)})
        assert result["status"] == "error"
    
    def test_pacing_check_included(self, tmp_path):
        """Test pacing check is included in output"""
        step = ScriptOutlineStep()
        result = step.execute({
            "topic_title": "ทดสอบจังหวะเวลา",
            "summary_bullets": ["ประเด็นทดสอบ"],
            "core_concepts": ["สติ"],
            "target_minutes": 10,
            "output_dir": str(tmp_path),
        })
        
        assert result["status"] == "success"
        assert "total_seconds" in result
        assert "within_target" in result
        assert result["total_seconds"] > 0
