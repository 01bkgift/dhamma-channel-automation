"""
ResearchRetrieval Pipeline Step
Wraps ResearchRetrievalAgent for orchestrator integration
Supports input_from to receive topics from TopicPrioritizer
"""

import json
import logging
from pathlib import Path
from typing import TypedDict

from agents.research_retrieval import (
    ResearchRetrievalAgent,
    ResearchRetrievalInput,
)
from agents.research_retrieval.model import ErrorResponse
from automation_core.base_step import BaseStep

logger = logging.getLogger(__name__)


class ResearchRetrievalContext(TypedDict, total=False):
    """Context for ResearchRetrievalStep"""

    # Input from previous step (via input_from in pipeline)
    input_file: str  # Path to topics_ranked.json or similar

    # Direct input (alternative to input_file)
    topic_title: str
    raw_query: str

    # Agent parameters
    refinement_hints: list[str]
    max_passages: int
    required_tags: list[str]
    forbidden_sources: list[str]
    context_language: str

    # Output location
    output_dir: str


class ResearchRetrievalStep(BaseStep):
    """Pipeline step for research and reference retrieval from dhamma sources"""

    def __init__(self):
        super().__init__(
            step_id="research_retrieval",
            step_type="ResearchRetrieval",
            version="1.0.0",
        )
        self.agent = ResearchRetrievalAgent()

    def execute(self, context: ResearchRetrievalContext) -> dict:
        """
        Execute research retrieval

        Input context (from input_from):
        - input_file: Path to topics_ranked.json from TopicPrioritizer

        Direct input (alternative):
        - topic_title: Topic title
        - raw_query: Search query

        Agent parameters:
        - refinement_hints: Hints for query refinement
        - max_passages: Maximum passages to retrieve (default: 12)
        - required_tags: Tags that must be present
        - forbidden_sources: Sources to exclude

        Output:
        - research_bundle.json: ResearchRetrievalOutput serialized
        """
        # Get topic from input_from file or direct input
        topic_title, raw_query = self._get_topic_input(context)

        if not topic_title or not raw_query:
            return {
                "status": "error",
                "error": "Missing topic_title or raw_query. Provide input_file or direct values.",
            }

        # Build agent input
        try:
            agent_input = ResearchRetrievalInput(
                topic_title=topic_title,
                raw_query=raw_query,
                refinement_hints=context.get("refinement_hints", []),
                max_passages=int(context.get("max_passages", 12)),
                required_tags=context.get("required_tags", []),
                forbidden_sources=context.get("forbidden_sources", []),
                context_language=context.get("context_language", "th"),
            )
        except Exception as e:
            self.logger.error(f"Failed to create agent input: {e}")
            return {"status": "error", "error": f"Invalid input parameters: {e}"}

        # Run agent
        self.logger.info(
            f"Running ResearchRetrieval for topic: {topic_title}, "
            f"max_passages: {agent_input.max_passages}"
        )
        result = self.agent.run(agent_input)

        # Handle error response
        if isinstance(result, ErrorResponse):
            self.logger.error(f"Agent returned error: {result.error}")
            return {
                "status": "error",
                "error": result.error.get("message", "Unknown error"),
                "error_code": result.error.get("code"),
                "suggested_fix": result.error.get("suggested_fix"),
            }

        # Save output
        output_dir = Path(context.get("output_dir", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "research_bundle.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        self.logger.info(
            f"Retrieved {result.stats.primary_count} primary + "
            f"{result.stats.supportive_count} supportive passages"
        )

        return {
            "status": "success",
            "output_file": str(output_path),
            "topic": result.topic,
            "primary_count": result.stats.primary_count,
            "supportive_count": result.stats.supportive_count,
            "coverage_confidence": result.coverage_assessment.confidence,
            "warnings": result.warnings,
        }

    def _get_topic_input(self, context: ResearchRetrievalContext) -> tuple[str, str]:
        """
        Extract topic and query from context.
        Priority: 1) Direct values, 2) From input_file
        """
        # Priority 1: Direct values
        topic_title = context.get("topic_title", "")
        raw_query = context.get("raw_query", "")

        if topic_title and raw_query:
            return topic_title, raw_query

        # Priority 2: From input_file (set by orchestrator via input_from)
        input_file = context.get("input_file")
        if input_file:
            input_path = Path(input_file)
            if input_path.exists():
                try:
                    with open(input_path, encoding="utf-8") as f:
                        data = json.load(f)

                    # Handle topics_ranked.json (from TopicPrioritizer)
                    topics = data.get("scheduled", data.get("topics", []))
                    if topics:
                        first_topic = topics[0]
                        topic_title = first_topic.get(
                            "topic_title", first_topic.get("title", "")
                        )
                        raw_query = first_topic.get("raw_query", topic_title)
                        return topic_title, raw_query
                except Exception as e:
                    self.logger.warning(f"Failed to read input file {input_path}: {e}")

        return topic_title, raw_query
