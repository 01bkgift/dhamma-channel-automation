from .agent_monitoring import AgentMonitoringStep
from .data_enrichment import DataEnrichmentStep
from .doctrine_validator import DoctrineValidatorStep
from .research_retrieval import ResearchRetrievalStep
from .security import SecurityStep
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
    "Security": SecurityStep,
    "ScriptOutline": ScriptOutlineStep,
    "ScriptWriter": ScriptWriterStep,
    "DoctrineValidator": DoctrineValidatorStep,
    "AgentMonitoring": AgentMonitoringStep,
}
