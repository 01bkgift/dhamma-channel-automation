# TrendScout Agent

## Overview

TrendScout analyzes trends from multiple sources and generates ranked content topic candidates for the Dhamma channel. It identifies high-opportunity topics by combining search data and trending content analysis.

## Features

- **Google Trends Integration**: Analyzes search trends in Thailand using `pytrends`.
- **YouTube Trending**: Identifies trending videos in Buddhist/mindfulness niche via YouTube Data API v3.
- **Multi-dimensional Scoring**: Evaluates topics on search intent, freshness, evergreen value, and brand fit.
- **Deterministic Output**: Produces consistent, reproducible results for the same inputs (when in mock mode).
- **Graceful Degradation**: Automatically falls back to high-quality mock data if external APIs are unavailable.

## Configuration

### Environment Variables

```bash
# Enable real API integration (default: false, uses mock data)
TREND_SCOUT_USE_REAL_APIS=true

# YouTube Data API key (required if USE_REAL_APIS=true)
YOUTUBE_API_KEY=your_api_key_here

# Google Trends (uses pytrends, no API key needed)
```

### API Requirements

1. **Google Trends**: Uses `pytrends` library (no API key required).
   - Rate limits: Automatic throttling is handled, but multiple rapid runs may trigger 429 errors.

2. **YouTube Data API v3**: Requires a Google Cloud API key.
   - Quota: Each run consumes approximately 11-20 units. Default daily quota is 10,000 units.

## Usage

### As Agent (Direct)

```python
from agents.trend_scout import TrendScoutAgent, TrendScoutInput

agent = TrendScoutAgent()

input_data = TrendScoutInput(
    keywords=["ปล่อยวาง", "เครียด", "สมาธิ"]
)

result = agent.run(input_data)

print(f"Generated {len(result.topics)} topics")
for topic in result.topics[:5]:
    print(f"{topic.rank}. {topic.title} (score: {topic.scores.composite:.2f})")
```

### As Pipeline Step

```yaml
steps:
  - id: trend_scout
    uses: TrendScout
    input:
      niches: ["dhamma", "mindfulness", "Buddhism (TH)"]
      horizon_days: 30
    output: trend_candidates.json
```

## Output Schema

See `src/agents/trend_scout/model.py` for the complete Pydantic schema.

```json
{
  "generated_at": "2024-01-15T10:30:00",
  "topics": [
    {
      "rank": 1,
      "title": "วิธีปล่อยวางตามหลักธรรม",
      "pillar": "ธรรมะประยุกต์",
      "predicted_14d_views": 15000,
      "scores": {
        "search_intent": 0.85,
        "freshness": 0.72,
        "evergreen": 0.68,
        "brand_fit": 0.90,
        "composite": 0.79
      },
      "reason": "ค้นหาสูง + เข้ากับแบรนด์",
      "raw_keywords": ["ปล่อยวาง", "ธรรม"]
    }
  ],
  "meta": {
    "total_candidates_considered": 45,
    "prediction_method": "median_trending * scaling_ratio",
    "self_check": {
      "duplicate_ok": true,
      "score_range_valid": true
    }
  }
}
```

## Testing

```bash
# Run unit tests (including API mocks)
pytest tests/test_trend_scout_agent.py -v

# Run step integration tests
pytest tests/steps/test_trend_scout_step.py -v

# Run end-to-end smoke test pipeline
python orchestrator.py pipelines/smoke_trend_scout.yaml
```

## Troubleshooting

### Issue: "Google Trends API failed"
- **Cause**: Rate limiting (HTTP 429) or network issues.
- **Solution**: The agent automatically falls back to internal logic/mock data. If persistent, wait 10-15 minutes.

### Issue: "YOUTUBE_API_KEY not set"
- **Cause**: Missing environment variable.
- **Solution**: Set `YOUTUBE_API_KEY` in your `.env` file or keep `TREND_SCOUT_USE_REAL_APIS=false`.

### Issue: "YouTube quota exceeded"
- **Cause**: Daily limit reached.
- **Solution**: Wait until the quota resets (midnight PST) or request a quota increase in the Google Cloud Console.

## Performance

- **Execution time**: ~10 seconds (with real APIs), <1 second (mock mode).
- **Network usage**: ~15 HTTP requests per run.
