from .data_enrichment import DataEnrichmentStep
from .research_retrieval import ResearchRetrievalStep
from .script_outline import ScriptOutlineStep
from .script_writer import ScriptWriterStep
from .topic_prioritizer import TopicPrioritizerStep
from .trend_scout import TrendScoutStep

# Register step for orchestrator
STEP_REGISTRY = {
    "TrendScout": TrendScoutStep,
    "TopicPrioritizer": TopicPrioritizerStep,
    "ResearchRetrieval": ResearchRetrievalStep,
    "DataEnrichment": DataEnrichmentStep,
    "ScriptOutline": ScriptOutlineStep,
    "ScriptWriter": ScriptWriterStep,
}
