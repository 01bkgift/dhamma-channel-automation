from .trend_scout import TrendScoutStep
from .topic_prioritizer import TopicPrioritizerStep
from .research_retrieval import ResearchRetrievalStep

# Register step for orchestrator
STEP_REGISTRY = {
    "TrendScout": TrendScoutStep,
    "TopicPrioritizer": TopicPrioritizerStep,
    "ResearchRetrieval": ResearchRetrievalStep,
}
