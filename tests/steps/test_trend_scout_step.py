"""
Tests for TrendScout pipeline step
"""

import json
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from steps.trend_scout import TrendScoutStep


class TestTrendScoutStep:
    """Test TrendScout pipeline step integration"""

    @pytest.fixture
    def step(self):
        return TrendScoutStep()

    @pytest.fixture
    def context(self, tmp_path):
        return {
            "niches": ["dhamma", "mindfulness"],
            "horizon_days": 30,
            "output_dir": str(tmp_path),
        }

    def test_step_initialization(self, step):
        """Test step initializes correctly"""
        assert step.step_id == "trend_scout"
        assert step.step_type == "TrendScout"
        assert step.version == "1.0.0"
        assert step.agent is not None

    def test_step_execute(self, step, context):
        """Test step execution"""
        result = step.execute(context)

        assert result["status"] == "success"
        assert "output_file" in result
        assert "topics_count" in result
        assert result["topics_count"] > 0

        # Verify output file
        output_file = Path(result["output_file"])
        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "topics" in data
            assert len(data["topics"]) > 0

    def test_step_with_custom_niches(self, step, context):
        """Test step with custom niche keywords"""
        context["niches"] = ["พุทธศาสนา", "สมาธิ", "วิปัสสนา"]

        result = step.execute(context)

        assert result["status"] == "success"
        assert result["topics_count"] > 0

    def test_step_output_schema(self, step, context):
        """Test output conforms to expected schema"""
        result = step.execute(context)

        output_file = Path(result["output_file"])
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate schema
        assert "generated_at" in data
        assert "topics" in data
        assert "meta" in data

        # Validate topics
        for topic in data["topics"]:
            assert "rank" in topic
            assert "title" in topic
            assert "pillar" in topic
            assert "predicted_14d_views" in topic
            assert "scores" in topic
            assert "reason" in topic
            assert "raw_keywords" in topic
