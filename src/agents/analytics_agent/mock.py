from typing import Any

from .adapter import YouTubeAnalyticsAdapter


class MockYouTubeAnalyticsAdapter(YouTubeAnalyticsAdapter):
    """Mock adapter for testing/dry-run"""

    def __init__(self):
        # No credentials needed
        pass

    def authenticate(self) -> bool:
        print("🔧 [MOCK] Authenticating...")
        return True

    def get_channel_stats(self, start_date: str, end_date: str) -> dict[str, Any]:
        print(f"🔧 [MOCK] Fetching channel stats: {start_date} to {end_date}")

        # Fake daily data for 30 days
        rows = []
        # Generate some dummy rows
        # Format: [day, views, estimatedMinutesWatched, subscribersGained, subscribersLost]
        # Just return one aggregated row for simplicity or a few
        rows.append(["2026-01-01", 1000, 5000, 10, 1])
        rows.append(["2026-01-02", 1500, 7500, 15, 2])
        rows.append(["2026-01-03", 2000, 10000, 20, 0])

        return {
            "kind": "youtubeAnalytics#resultTable",
            "columnHeaders": [],
            "rows": rows,
        }

    def get_recent_videos(self, max_results: int = 10) -> list[dict[str, Any]]:
        print(f"🔧 [MOCK] Fetching recent {max_results} videos")

        videos = []
        for i in range(5):
            videos.append(
                {
                    "kind": "youtube#video",
                    "id": f"vid_00{i}",
                    "snippet": {
                        "publishedAt": "2026-01-01T10:00:00Z",
                        "title": f"Mock Video {i + 1} - Dhamma Talk",
                        "description": "Description...",
                        "channelId": "channel_id",
                        "thumbnails": {
                            "default": {"url": "http://example.com/thumb.jpg"}
                        },
                    },
                    "statistics": {
                        "viewCount": str(1000 * (i + 1)),
                        "likeCount": str(50 * (i + 1)),
                        "dislikeCount": "0",
                        "favoriteCount": "0",
                        "commentCount": str(10 * (i + 1)),
                    },
                }
            )

        return videos
