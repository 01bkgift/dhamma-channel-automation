"""
TrendScout Pipeline Step
Wraps TrendScoutAgent for orchestrator integration
"""

import json
import logging
from pathlib import Path
from typing import TypedDict

from agents.trend_scout import TrendScoutAgent, TrendScoutInput
from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)


class TrendScoutContext(TypedDict, total=False):
    """Context for TrendScoutStep"""

    niches: list[str]
    horizon_days: int
    output_dir: str


class TrendScoutStep(BaseStep):
    """Pipeline step for trend analysis and topic generation"""

    def __init__(self):
        super().__init__(step_id="trend_scout", step_type="TrendScout", version="1.0.0")
        self.agent = TrendScoutAgent()

    def execute(self, context: TrendScoutContext) -> dict:
        """
        Execute trend scouting

        Input context:
        - niches: list[str] - Niche keywords (e.g., ["dhamma", "mindfulness"])
        - horizon_days: int - Time horizon for trends (default: 30)

        Output:
        - trend_candidates.json: TrendScoutOutput serialized
        """
        # Parse input
        niches = context.get("niches", ["dhamma", "mindfulness", "Buddhism (TH)"])
        # horizon_days = context.get("horizon_days", 30) # Not used in current agent implementation but kept for future

        # Prepare agent input
        agent_input = TrendScoutInput(
            keywords=niches,
            google_trends=[],  # Will be fetched by agent
            youtube_trending_raw=[],  # Will be fetched by agent
            competitor_comments=[],
            embeddings_similar_groups=[],
        )

        # Run agent
        self.logger.info(f"Running TrendScout with niches: {niches}")
        result = self.agent.run(agent_input)

        # Save output
        output_dir = Path(context.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "trend_candidates.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        self.logger.info(f"Generated {len(result.topics)} topic candidates")

        return {
            "status": "success",
            "output_file": str(output_path),
            "topics_count": len(result.topics),
            "top_topic": result.topics[0].title if result.topics else None,
        }
