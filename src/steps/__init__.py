from .trend_scout import TrendScoutStep

# Register step for orchestrator
STEP_REGISTRY = {
    "TrendScout": TrendScoutStep,
}
