"""
Integration tests for ResearchRetrievalStep with input_from support
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from steps.research_retrieval import ResearchRetrievalStep


class TestResearchRetrievalStep:
    """Test suite for ResearchRetrievalStep"""

    def test_step_initialization(self):
        """Test step can be instantiated"""
        step = ResearchRetrievalStep()
        assert step.step_id == "research_retrieval"
        assert step.step_type == "ResearchRetrieval"
        assert step.version == "1.0.0"

    def test_execute_with_direct_input(self, tmp_path):
        """Test execution with direct topic and query"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "topic_title": "ปล่อยวางก่อนนอน",
                "raw_query": "วิธีปล่อยวางก่อนนอนจากหลักธรรม",
                "output_dir": str(tmp_path),
                "max_passages": 10,
            }
        )

        assert result["status"] == "success"
        assert "output_file" in result
        assert Path(result["output_file"]).exists()
        assert result["primary_count"] >= 0

    def test_execute_with_input_from(self, tmp_path):
        """Test execution with input_from (TopicPrioritizer format)"""
        # Create mock topics_ranked.json (TopicPrioritizer output)
        mock_data = {
            "scheduled": [
                {
                    "topic_title": "การมีสติในชีวิตประจำวัน",
                    "pillar": "ธรรมะประยุกต์",
                    "week": 1,
                    "day": "monday",
                }
            ],
            "unscheduled": [],
        }

        input_file = tmp_path / "topics_ranked.json"
        input_file.write_text(
            json.dumps(mock_data, ensure_ascii=False), encoding="utf-8"
        )

        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "input_file": str(input_file),
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert result["topic"] == "การมีสติในชีวิตประจำวัน"

    def test_execute_with_refinement_hints(self, tmp_path):
        """Test with refinement hints"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "topic_title": "การทำสมาธิ",
                "raw_query": "วิธีทำสมาธิ อานาปานสติ",
                "refinement_hints": ["เน้นหลักคำสอน", "เกี่ยวกับปฏิบัติ"],
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        output = json.loads(Path(result["output_file"]).read_text(encoding="utf-8"))
        assert len(output["queries_used"]) > 1  # Base + refinements

    def test_execute_with_required_tags(self, tmp_path):
        """Test with required tags filter"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "topic_title": "สติและความสงบ",
                "raw_query": "สติ ปล่อยวาง",
                "required_tags": ["สติ"],
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"

    def test_missing_input(self, tmp_path):
        """Test error handling for missing input"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "error"
        assert "Missing" in result["error"]

    def test_missing_input_file(self, tmp_path):
        """Test with nonexistent input_file falls back gracefully"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "input_file": str(tmp_path / "nonexistent.json"),
                "output_dir": str(tmp_path),
            }
        )

        # Should error because no topic was provided
        assert result["status"] == "error"

    def test_coverage_confidence_returned(self, tmp_path):
        """Test that coverage confidence is in result"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "topic_title": "ปล่อยวาง",
                "raw_query": "การปล่อยวาง",
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert "coverage_confidence" in result
        assert 0.0 <= result["coverage_confidence"] <= 1.0

    def test_warnings_returned(self, tmp_path):
        """Test that warnings list is in result"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "topic_title": "หัวข้อทดสอบ",
                "raw_query": "คำค้นทดสอบ",
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_output_file_structure(self, tmp_path):
        """Test output file has correct structure"""
        step = ResearchRetrievalStep()
        result = step.execute(
            {
                "topic_title": "ธรรมะก่อนนอน",
                "raw_query": "หลักธรรมเพื่อการนอนหลับ",
                "output_dir": str(tmp_path),
            }
        )

        assert result["status"] == "success"
        output = json.loads(Path(result["output_file"]).read_text(encoding="utf-8"))

        # Check required fields
        assert "topic" in output
        assert "queries_used" in output
        assert "primary" in output
        assert "supportive" in output
        assert "summary_bullets" in output
        assert "coverage_assessment" in output
        assert "stats" in output
        assert "meta" in output
