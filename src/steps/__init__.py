from .trend_scout import TrendScoutStep
from .topic_prioritizer import TopicPrioritizerStep
from .research_retrieval import ResearchRetrievalStep
from .data_enrichment import DataEnrichmentStep
from .script_outline import ScriptOutlineStep

# Register step for orchestrator
STEP_REGISTRY = {
    "TrendScout": TrendScoutStep,
    "TopicPrioritizer": TopicPrioritizerStep,
    "ResearchRetrieval": ResearchRetrievalStep,
    "DataEnrichment": DataEnrichmentStep,
    "ScriptOutline": ScriptOutlineStep,
}
